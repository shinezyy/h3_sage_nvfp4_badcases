#!/usr/bin/env bash
set -euo pipefail
export HF_HOME=/models/hf
export SGLANG_CACHE_DIT_ENABLED=false
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
python3 - <<'PYMODEL'
from huggingface_hub import snapshot_download
snapshot_download('MiniMaxAI/MiniMax-H3', local_dir='/models/MiniMax-H3', allow_patterns=['*.json', '*.txt', '*.model', '*.tiktoken'])
snapshot_download('lilcheaty/MiniMax-H3-NVFP4', allow_patterns=['minimax_h3_fl2va_pruned_nvfp4.safetensors', 'text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors', 'vae/minimax_h3_video_vae_fp16.safetensors', 'vae/minimax_h3_audio_vae_fp32.safetensors'])

PYMODEL
exec sglang serve --model-type diffusion --model-path /models/MiniMax-H3 --served-model-name MiniMaxAI/MiniMax-H3 --model-variant fl2va --component-weights-paths.transformer lilcheaty/MiniMax-H3-NVFP4/minimax_h3_fl2va_pruned_nvfp4.safetensors --component-weights-paths.text_encoder lilcheaty/MiniMax-H3-NVFP4/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors --component-weights-paths.video_vae lilcheaty/MiniMax-H3-NVFP4/vae/minimax_h3_video_vae_fp16.safetensors --component-weights-paths.audio_vae lilcheaty/MiniMax-H3-NVFP4/vae/minimax_h3_audio_vae_fp32.safetensors --num-gpus 1 --ulysses-degree 1 --performance-mode manual --text-encoder-cpu-offload true --vae-cpu-offload true --attention-backend sage_attn --enable-torch-compile false --warmup-mode off --host 0.0.0.0 --port 30010 --output-path /models/output --component-attention-backends text_encoder=torch_sdpa
