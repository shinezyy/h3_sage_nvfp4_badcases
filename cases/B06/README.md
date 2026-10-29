# B06 — baseline failure and improved simplified-prompt comparison

The baseline has an extra introductory phrase before the intended dialogue. In the simplified-prompt output, automatic transcription contains only the intended mother's question and child's response. This case is included as an improved comparison, not as a persistent extra-speech failure. Requested local speaking windows are still not followed exactly.

[Exact simplified prompt](prompt.txt) · [Request](request.json) · [Simplified output](output.mp4)

| First frame | Last frame |
|---|---|
| ![First](first.png) | ![Last](last.png) |

## Expected dialogue

妈妈：你觉得老师太严厉了，是吗？
主角：嗯，我不舒服。

## Automatic transcripts

Baseline: 男老的催他快一点,自己有点怕你觉得老师太严厉了,是吗?嗯,我不舒服

Simplified prompt: 你觉得老师太严厉了,是吗?嗯,我不舒服

[Original prompt](baseline/prompt.txt) · [Original problematic video](baseline/output.mp4)

The baseline and simplified trial use the same frame bytes, seed, requested duration (10 s), steps, resolution and server configuration. Several prompt fields change together, including removal of music; this is not a single-variable ablation. ASR is approximate and can hallucinate; it does not establish the absence of all noise, overlap, or voice-quality problems.

These videos are from the earlier prompt experiment. No video has yet been generated for the later shortened/resegmented storyboard.
