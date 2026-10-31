#!/usr/bin/env python3
"""Compile reviewed English scene prose using the pinned official H3 FL2VA format."""
import copy
import csv
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIELDS = ('integrated_multimodal_description', 'overall_soundscape', 'non_diegetic_music')
VOICES = {
    '旁白': ('S1', 'An adult female narrator who is never visible, with a warm mid-register voice and clear, evenly paced Mandarin'),
    '主角': ('S2', 'The yellow-shirted preschool boy with teal trousers, speaking Mandarin in a light, high-pitched child voice'),
    '同学A': ('S3', 'The coral-shirted preschool boy, speaking Mandarin in a bright, slightly lower child voice'),
    '同学B': ('S4', 'The lavender-shirted preschool girl with two braids, speaking Mandarin in a light, clear child voice'),
    '老师': ('S5', 'The adult female teacher in a mint cardigan, speaking Mandarin in a clear mid-register voice'),
    '妈妈': ('S6', 'The adult mother in a peach top, speaking Mandarin in a soft, warm lower-mid-register voice'),
}
SHORT = {'旁白': 'The narrator', '主角': 'The yellow-shirted boy', '同学A': 'The coral-shirted boy',
         '同学B': 'The lavender-shirted girl', '老师': 'The teacher', '妈妈': 'The mother'}
SOUNDS = ('Ambient room or outdoor noise, footsteps, object impacts and non-verbal human sounds are inaudible. '
          'The brief gaps between the specified vocal events are silent.')


def read(path):
    return json.loads(path.read_text())


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clock(value):
    milliseconds = round(value * 1000)
    return f'{milliseconds // 60000:02d}:{milliseconds // 1000 % 60:02d}.{milliseconds % 1000:03d}'


def speech(role, text, start, end, seen):
    sid, definition = VOICES[role]
    who = SHORT[role] if role in seen else definition
    who = who[0].lower() + who[1:]
    seen.add(role)
    verb = 'says in an off-screen voiceover' if role == '旁白' else 'says'
    suffix = ' while all on-screen characters\' lips remain completely closed.' if role == '旁白' else ' The other visible characters listen with their lips closed.'
    return f'From {clock(start)} to {clock(end)}, {who} ({sid}) {verb}: <d>[Chinese] {text}</d>{suffix}'


def render(segment, scene):
    seconds = segment['seconds']
    utterances = segment['utterances']
    assert len(scene['beats']) == len(utterances), segment['id']
    seen = set()
    shot_count = 2 if segment['id'] == 'RP01' else 1
    first_line = ('How the reference pictures align with the target video — Picture 1 (from Shot 1) '
                  'aligns with the 0.00-second mark of the target video; '
                  f'Picture 2 (from Shot {shot_count}) aligns with the {seconds:.2f}-second mark of the target video.')
    opening = scene['opening']
    assert 'Picture 1' in opening and 'Picture 2' in scene['ending'], segment['id']
    body = '[Shot 1] ' + opening
    if segment['id'] == 'RP01':
        u = utterances[0]
        prefix = '在幼儿园里，小朋友会'
        assert u['text'].startswith(prefix)
        cut = 4.0
        body += ' ' + scene['beats'][0] + ' '
        body += speech(u['speaker'], prefix + '<scenetrans>', u['start'], cut, seen)
        body += ' The narration continues seamlessly across the cut. '
        body += '[Shot 2] At 00:04.000, the camera cuts to ' + scene['second_shot_opening'] + ' '
        body += 'The same narration carries over from the previous shot without a restart or a pause. '
        body += speech(u['speaker'], '<scenetrans>' + u['text'][len(prefix):], cut, u['end'], seen)
    else:
        for u, beat in zip(utterances, scene['beats']):
            body += ' ' + beat + ' ' + speech(u['speaker'], u['text'], u['start'], u['end'], seen)
    body += (' ' + scene['ending'] + f' Reach this final composition at {clock(seconds)}. '
             'Each written vocal event occurs once in the given order, with no overlapping voices. '
             'The opening, short gaps and final settling moment contain no speech. No subtitles or other written text appear.')
    return first_line + '\n\n' + f'{FIELDS[0]}: {body}\n\n{FIELDS[1]}: {SOUNDS}\n\n{FIELDS[2]}: N/A\n'


def validate(prompt, s):
    """Check output semantics, not just whether the generator completed."""
    ids = re.findall(r'\[Shot (\d+)\]', prompt)
    assert ids == (['1', '2'] if s['id'] == 'RP01' else ['1']), (s['id'], ids)
    assert not re.search(r'\[Shot 1\]\s+(?:At\s+\d|From\s+\d|\d\d:)', prompt)
    assert f'aligns with the {s["seconds"]:.2f}-second mark' in prompt.splitlines()[0]
    assert prompt.splitlines()[1] == ''
    assert re.findall(r'^([a-z_]+):', prompt, re.M) == list(FIELDS)
    chunks = re.findall(r'<d>\[Chinese\] (.*?)</d>', prompt)
    normalized = [t.replace('<scenetrans>', '') for t in chunks]
    expected = [u['text'] for u in s['utterances']]
    assert ''.join(normalized) == ''.join(expected), (s['id'], 'verbatim dialogue')
    if s['id'] != 'RP01':
        assert normalized == expected, (s['id'], 'utterance ordering')
        assert '<scenetrans>' not in prompt
    else:
        assert prompt.count('<scenetrans>') == 2
    assert '<cutoff>' not in prompt
    assert not re.search(r'[\u4e00-\u9fff]', re.sub(r'<d>.*?</d>', '', prompt)), s['id']
    assert set(re.findall(r'\((S\d+)\)', prompt)) == {VOICES[u['speaker']][0] for u in s['utterances']}
    for block in re.findall(r'says in an off-screen voiceover: <d>.*?</d>([^.]*\.)', prompt):
        assert 'lips remain completely closed' in block
    ranges = re.findall(r'From (\d\d:\d\d\.\d{3}) to (\d\d:\d\d\.\d{3})', prompt)
    previous = 0
    def numeric(t):
        minutes, secs = t.split(':')
        return int(minutes) * 60 + float(secs)
    for start, end in ranges:
        a, b = numeric(start), numeric(end)
        assert previous <= a < b <= s['seconds'], (s['id'], 'time range')
        previous = b
    assert len(ranges) == len(chunks)
    assert len(prompt.split('overall_soundscape: ', 1)[1].split('\n\n')[0].split('. ')) <= 4
    assert prompt.endswith('non_diegetic_music: N/A\n')


def main():
    baseline = read(ROOT / 'source/storyboard-v2.json')
    original = read(ROOT / 'source/storyboard-original.json')
    old_manifest = read(ROOT / 'source/manifest-v2.json')
    sources = {s['id']: s for s in original['segments']}
    scenes = {}
    for filename in ('scene-a.json', 'scene-b.json', 'scene-c-e.json'):
        part = read(ROOT / filename)
        assert not scenes.keys() & part.keys()
        scenes.update(part)
    segments = copy.deepcopy(baseline['segments'])
    assert set(scenes) == {s['id'] for s in segments}
    assert [i for s in segments for i in s['source_ids']] == list(sources)
    (ROOT / 'prompts').mkdir(exist_ok=True)
    hashes, records, cards, changes = {}, [], [], []
    for s in segments:
        # The official guide preserves original punctuation as well as words.
        # v2 changed two terminal commas; restore them from the original source here.
        for u in s['utterances']:
            fragments = []
            for ref in u['sources']:
                line = sources[ref['segment']]['lines'][ref['line'] - 1]
                role, text = line.split('：', 1)
                assert role == u['speaker'] and text == ref['text']
                fragments.append(text)
            actual = ''.join(fragments)
            if actual != u['text']:
                changes.append({'clip': s['id'], 'before': u['text'], 'after': actual, 'reason': 'Restore original punctuation verbatim per official guide'})
            u['text'] = actual
        assert ''.join(u['text'] for u in s['utterances']) == ''.join(line.split('：', 1)[1] for i in s['source_ids'] for line in sources[i]['lines'])
        prompt = render(s, scenes[s['id']])
        validate(prompt, s)
        output = ROOT / 'prompts' / (s['id'] + '.txt')
        output.write_text(prompt)
        hashes[str(output.relative_to(ROOT))] = digest(output)
        for key in ('first_frame', 'last_frame'):
            path = ROOT / s[key]
            assert path.is_file()
            # Bundled frames must match the original reviewed inputs.
            assert digest(path) == read(ROOT / 'source/frame-sha256.json')[s[key]]
            hashes[s[key]] = digest(path)
        assert 4 <= s['seconds'] <= 15
        s['official_scene'] = scenes[s['id']]
        s['prompt_file'] = str(output.relative_to(ROOT))
        s['input_mode'] = 'FL2VA'
        s['punctuation_edits'] = []
        records.append({'id': s['id'], 'source_ids': s['source_ids'], 'seconds': s['seconds'], 'speakers': sorted({VOICES[u['speaker']][0] for u in s['utterances']}), 'shots': 2 if s['id'] == 'RP01' else 1, 'checks': 'passed'})
        subtitle = f"{s['id']} · {' + '.join(s['source_ids'])} · {s['seconds']}s"
        frames = ''.join(f'<figure><img loading="lazy" src="{s[k]}"><figcaption>{label}: {Path(s[k]).stem}</figcaption></figure>' for k, label in [('first_frame', 'Picture 1'), ('last_frame', 'Picture 2')])
        dialogue = '\n'.join(f"{clock(u['start'])}–{clock(u['end'])} {u['speaker']}: {u['text']}" for u in s['utterances'])
        old = (ROOT / 'source/prompts-v2' / (s['id'] + '.txt')).read_text()
        cards.append(f'<article id="{s["id"]}"><h2>{subtitle}</h2>{frames}<h3>原文对白（核对用，不重复提交）</h3><pre>{html.escape(dialogue)}</pre><h3>官方格式完整 prompt</h3><pre>{html.escape(prompt)}</pre><details><summary>与旧版 prompt 对照</summary><pre>{html.escape(old)}</pre></details></article>')
    jobs = [{'id': s['id'], 'prompt_file': s['prompt_file'], 'first_frame': s['first_frame'], 'last_frame': s['last_frame'], 'seconds': s['seconds']} for s in segments]
    assert jobs == old_manifest['jobs'], 'Only prompt content should change, not job settings/paths/order'
    manifest = {'defaults': old_manifest['defaults'], 'jobs': jobs}
    save(ROOT / 'manifest.json', manifest)
    save(ROOT / 'pilot-manifest.json', {**manifest, 'jobs': [j for j in jobs if j['id'] in ('RA01', 'RA04', 'RB06')]})
    save(ROOT / 'storyboard.json', {'status': 'official_skill_rewrite_not_generated', 'stats': baseline['stats'], 'skill_source': read(ROOT / 'skill-source.json'), 'speaker_ids': {k: v[0] for k, v in VOICES.items()}, 'segments': segments})
    for path in (ROOT / 'source').glob('*.json'):
        hashes[str(path.relative_to(ROOT))] = digest(path)
    source = read(ROOT / 'skill-source.json')
    for path, sha in source['upstream_files_sha256'].items():
        assert digest(ROOT / path) == sha
    save(ROOT / 'validation.json', {'status': 'offline_passed', 'clips': len(jobs), 'original_segments_covered_once_in_order': len(sources), 'total_seconds': sum(j['seconds'] for j in jobs), 'all_original_dialogue_and_punctuation_verbatim': True, 'all_fields_and_speaker_tags_valid': True, 'all_frame_paths_and_settings_unchanged': True, 'punctuation_restorations_from_v2': changes, 'checks_by_clip': records, 'input_and_prompt_sha256': hashes, 'inference_performed': False})
    with (ROOT / 'mapping.csv').open('w') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(['id', 'source_ids', 'seconds', 'first_frame', 'last_frame', 'prompt'])
        for s in segments:
            writer.writerow([s['id'], '+'.join(s['source_ids']), s['seconds'], s['first_frame'], s['last_frame'], s['prompt_file']])
    (ROOT / 'all-prompts.md').write_text('# Official H3 FL2VA prompts — 31 clips\n\n' + '\n\n'.join(f"## {s['id']} ({s['seconds']} seconds)\n\n```text\n{(ROOT/s['prompt_file']).read_text()}```" for s in segments) + '\n')
    (ROOT / 'index.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>H3 官方格式 v3</title><style>body{max-width:1150px;margin:32px auto;padding:0 20px;font:16px/1.6 system-ui;background:#f5f4ee;color:#24302c}article{background:white;margin:24px 0;padding:24px;border-radius:12px}figure{display:inline-block;width:46%;margin:1%}img{width:100%}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.7 ui-monospace,monospace}summary{cursor:pointer}nav a{margin-right:12px}</style><h1>H3 官方格式重写 v3</h1><p>31 段 / 5分10秒，覆盖原 44 段。首尾帧及生成参数沿用紧凑版 v2。说明为英文，所有原对白及标点原样保留。</p><p>本页为输入审核；尚未生成或验证音频改善。对白核对栏不进入模型输入。</p><p><a href="README.md">说明</a> · <a href="manifest.json">完整清单</a> · <a href="pilot-manifest.json">三段试验</a> · <a href="all-prompts.md">所有 prompts</a></p><nav>' + ''.join(f'<a href="#{s["id"]}">{s["id"]}</a>' for s in segments) + '</nav>' + ''.join(cards) + '</html>')
    print(f'Validated {len(jobs)} clips, {sum(j["seconds"] for j in jobs)} seconds, covering all {len(sources)} original segments; {len(changes)} punctuation restorations.')


if __name__ == '__main__':
    main()
