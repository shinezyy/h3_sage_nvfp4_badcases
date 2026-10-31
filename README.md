# h3_sage_nvfp4_badcases

Three previously problematic MiniMax-H3 FL2VA clips with SageAttention + NVFP4, **Cache-DiT disabled**, tracking both original and simplified prompts. A02 and A04 still exhibit audio failures; B06 improved in the simplified-prompt trial. These artifacts do not establish that SageAttention or NVFP4 caused the failures.

| Case | Duration requested | Observed problem | Exact prompt |
|---|---:|---|---|
| [A02](cases/A02/) | 10 s | Extra speech-like content after correct dialogue; silence instruction not followed | [prompt.txt](cases/A02/prompt.txt) |
| [A04](cases/A04/) | 13 s | Child reply repeated; speaking windows not strictly followed | [prompt.txt](cases/A04/prompt.txt) |
| [B06](cases/B06/) | 10 s | Baseline has an extra introduction; simplified output contains only intended dialogue in ASR | [prompt.txt](cases/B06/prompt.txt) |

## Video downloads

| Clip | Original problematic video | Simplified-prompt video |
|---|---|---|
| A02 | [MP4](cases/A02/baseline/output.mp4) | [MP4](cases/A02/output.mp4) |
| A04 | [MP4](cases/A04/baseline/output.mp4) | [MP4](cases/A04/output.mp4) |
| B06 | [MP4](cases/B06/baseline/output.mp4) | [MP4](cases/B06/output.mp4) |

These are the earlier generated clips. The later shortened/resegmented storyboard has not yet been generated.

## Official-skill rewrite (v3, not yet generated)

The complete storyboard is rewritten using the official MiniMax H3 FL2VA prompt-writing skill: **31 clips, 310 seconds**, covering all 44 original segments. Original dialogue and punctuation are preserved, with English descriptions, stable speaker IDs, dialogue tags, and explicit first/last-frame alignment.

- [All 31 prompts](storyboards/official_h3_v3/all-prompts.md)
- [Version notes and rebuild instructions](storyboards/official_h3_v3/README.md)
- [Full manifest](storyboards/official_h3_v3/manifest.json) · [Three-clip pilot](storyboards/official_h3_v3/pilot-manifest.json)
- [Reference frames](storyboards/frames/) · [Original-to-revised mapping](storyboards/official_h3_v3/mapping.csv)

This package includes the 33 reused reference images, frozen source scripts, previous prompts for comparison, and the pinned official skill. Local checks passed; no v3 videos or audio-quality improvements have been validated yet.

Each case tracks the exact UTF-8 prompt, first/last PNG keyframes, actual generated MP4, request parameters, SHA-256, timing, and automatic audio transcription. `baseline/` preserves the earlier longer prompt and video for comparison. Only image URIs in `request.json` were rewritten to portable container paths; prompt and other request parameters are unchanged. Output bytes are unchanged. Model weights and container layers are not included.

## Reproduction

Requirements: a compatible Blackwell GPU, Docker with NVIDIA runtime, enough host RAM for CPU offload, disk space for roughly 34 GB selected weights plus the large SGLang image. The observed GPU was RTX PRO 6000 with 96 GB VRAM; generation used roughly 31 GB reported peak memory. No GPU allocation is performed by these scripts.

```bash
# Build the supplied SageAttention SM120/C++20 recipe (CPU build is possible).
docker build -t h3-sage-nvfp4:local reproduction/
mkdir -p models
# Mount this repository's cases at /cases, and persistent model storage at /models.
docker run --rm --init --gpus device=0 --shm-size=16g \
  -p 127.0.0.1:30010:30010 \
  -v "$PWD/models:/models" -v "$PWD/cases:/cases:ro" \
  -v "$PWD/reproduction:/reproduction:ro" \
  --entrypoint bash h3-sage-nvfp4:local /reproduction/serve.sh

# Another terminal: print the portable JSON, then explicitly submit.
python3 reproduction/reproduce.py A02
python3 reproduction/reproduce.py A02 --submit
python3 reproduction/reproduce.py A04 --submit
python3 reproduction/reproduce.py B06 --submit
```

The server startup downloads only base configs/tokenizers and four selected component weights. Keep the local base directory name `MiniMax-H3`; this name is required for native pipeline detection in the observed image. Requests omit `quality`. Inputs are keyframes at indices 0 and -1. Defaults: 480 short edge, 16:9, 50 steps, seed 20261028, flow shift 12, audio flow shift 3.

`environment.json` records observed package versions and image digest. The published original image is private; the included Docker build recipe reflects the current cache-off helper and is not byte-for-byte the published image. Downloaded model revisions were not pinned/captured for this trial, so exact deterministic reproduction across future downloads is not guaranteed. Reproduction scripts were checked locally without launching another GPU generation.

## Evidence limits

Transcription used local Whisper large-v3-turbo in MLX, Chinese, temperature=0, with no expected dialogue supplied. ASR can hallucinate on music, noises, or unclear voices. Times are approximate and results do not establish speaker identity, overlap, or subjective sound quality. This is one fixed seed per case with a combined prompt intervention, not a causal test of individual prompt fields or attention/quantization backends.

## Integrity

```bash
python3 reproduction/verify.py
```

See `SHA256SUMS` for committed data and reproduction file hashes. No cloud account credentials, VM addresses, SSH keys, or private registry login data are included.
