# MiniMax H3 官方 skill 重写版 v3

当前完整紧凑版的 **31 段、310 秒（5分10秒）** 全部重写，按序覆盖原始 44 段。此版本直接应用 MiniMax 官方 `h3-prompt-writing` 的 **FL2VA** 分支，输入仍为两张首尾帧。

## 查看与使用

- [逐段预览](index.html)：首尾图、对白核对、完整新 prompt、旧 prompt 对照。
- [全部 prompt](all-prompts.md) / [prompts/](prompts/)：提交给模型的完整文本。
- [完整批次 manifest.json](manifest.json)：31 段，沿用既有 batch runner。
- [三段试验 pilot-manifest.json](pilot-manifest.json)：RA01（原 A01+A02）、RA04、RB06（原 B06+B07）。
- [mapping.csv](mapping.csv)：31 段与原 44 段的映射；[storyboard.json](storyboard.json) 保留逐句来源和局部时间。
- [validation.json](validation.json)：对白、字段、标签、时长和输入文件检查；运行 runner 后另有 `batch-validation.json`。

这里的“全部”指当前已重新分镜的 31 段，不是把原 44 段旧时长重新跑一遍。现有原始视频、v2 输入和公开 badcase 仓库均保留。

## 官方来源

- [官方 SKILL.md](https://github.com/MiniMax-AI/MiniMax-H3/blob/199b7d0e1fd95e7b3eafa8c15eca692534142427/skills/h3-prompt-writing/SKILL.md)
- [官方 base-en.txt](https://github.com/MiniMax-AI/MiniMax-H3/blob/199b7d0e1fd95e7b3eafa8c15eca692534142427/skills/h3-prompt-writing/references/base-en.txt)

读取日期：2026-10-31。固定上游提交 `199b7d0e1fd95e7b3eafa8c15eca692534142427`，原文快照位于 `upstream/h3-prompt-writing/`；`skill-source.json` 记录来源与文件哈希。三个 sub-agent 分幕撰写英文画面与动作，主代理统一格式、对白及验证。没有安装或执行第三方脚本。

## 实际修改

1. 使用官方首行 FL2VA 对齐声明，Picture 1 对应 0.00 秒，Picture 2 对应本段时长，精确到两位小数。
2. 按官方顺序填写 `integrated_multimodal_description`、`overall_soundscape`、`non_diegetic_music`。画面、动作、声音说明均用英文。
3. 对白只放在 `<d>[Chinese] …</d>` 内，角色名称、语气、时间不放进可朗读文本。以原始剧本为准逐字保留所有文字和标点；恢复 v2 将 C02/C03 末尾逗号改成句号的两处修改。连续同一说话人的原条目可以合并，但不增删字句。
4. 全片固定身份：S1 旁白、S2 主角、S3 同学 A、S4 同学 B、S5 老师、S6 妈妈。每段只给实际发声者编号，并在第一次发声时明确外形/画外来源、音色及语言；不发声人物不分配编号。
5. 旁白使用官方要求的画外发声短语；每个旁白块后紧接所有画中人物闭嘴的说明。片头沿用已有外景到教室的切镜，设于 `00:04.000`，旁白跨切点两端均使用 `<scenetrans>`；其余 30 段单镜头连续运动到尾帧。
6. 保留 v2 的局部发声窗口、儿童原有结巴与停顿，只有相应人物发声。无配乐（音乐字段为 `N/A`），无额外环境声、哭声或碰撞音效。音景字段仍以英文描述，不能因为没有配乐就把整段声景标为 `N/A`。

## 保持不变

- 31 段的顺序、时长预算、首尾帧路径以及图片字节；直接复用 `../frames/`，新增图片为零。
- 480 短边、16:9、50 steps、seed 20261028。使用之前准备的 SageAttention 镜像，Cache-DiT 仍关闭。
- 原始台词含义、字词、顺序；没有加前情、另加角色台词或后期字幕。

英文音色描述只是 prompt 中的一致性约束，没有提供声音参考，因此不能保证不同生成任务的音色完全一致。局部时间窗同样是软提示，不是服务端强制切分音频。

## 离线复现与预检

下载或 clone 本仓库后，从本目录执行：

```bash
python3 build.py
python3 ../../reproduction/verify.py
```

`build.py` 使用 `source/` 中冻结的原始剧本、v2 剧本和 prompts，以及三个分幕英文场景文件重建全部输入与预览。`../frames/` 包含本批次引用的全部 33 张现有图片；图片字节与本地审核版本一致。可在本地浏览器打开 `index.html`；GitHub 上直接阅读 `all-prompts.md`。

脚本检查全部原片段按序覆盖、对白及标点原样保留、仅对白包含中文、三个官方字段顺序、说话人编号、镜头及时间标记、图片存在与哈希。`batch-validation.json` 记录本次对公开目录中的清单进行实际 batch runner 离线预检的结果。批次 runner 属于外部 Nebius 工作流，未捆绑在本仓库；已有该 runner 的用户可以将 `manifest.json` 或 `pilot-manifest.json` 传给它，使用新的 batch ID，并指定 SageAttention、关闭 Cache-DiT。真实生成仍需兼容的 GPU 与有效的服务配置。

**当前未生成新视频，不能据此断言原音频问题的根因已经找到或得到修复。** 官方格式是本次待验证的改动；应先试三段再决定全量运行。因为本版本相对之前已生成的旧案例还包括紧凑版时长及合并方式的变化，不能把新旧视频差异全部归因于官方格式。若要隔离格式因素，需以相同的 v2 时长、帧、seed 和参数分别生成两个版本。
