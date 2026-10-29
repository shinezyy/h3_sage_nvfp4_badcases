#!/usr/bin/env bash
# SageAttention recipe validated on RTX PRO 6000, 2026-10-29.
# Run inside the SGLang container with the models already under /work/models.
# The screenshot specifies sageattention==2.2.0. Its comfy-kitchen version is
# clipped; the earlier saved recipe uses comfy-kitchen==0.2.40.
# Screenshot note: omit `quality` from generation requests; explicitly setting
# it disables the generic H3 Cache-DiT path in that environment.
set -euo pipefail

export HF_HOME=/work/hf
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

export SGLANG_CACHE_DIT_ENABLED=${SGLANG_CACHE_DIT_ENABLED:-false}
export SGLANG_CACHE_DIT_FN=1
export SGLANG_CACHE_DIT_BN=0
export SGLANG_CACHE_DIT_WARMUP=4
export SGLANG_CACHE_DIT_RDT=0.12
export SGLANG_CACHE_DIT_MC=2

exec sglang serve --model-type diffusion \
  --model-path /work/models/MiniMax-H3 \
  --served-model-name MiniMaxAI/MiniMax-H3 \
  --model-variant fl2va \
  --component-weights-paths.transformer /work/models/lilcheaty/minimax_h3_fl2va_pruned_nvfp4.safetensors \
  --component-weights-paths.text_encoder /work/models/lilcheaty/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors \
  --component-weights-paths.video_vae /work/models/lilcheaty/vae/minimax_h3_video_vae_fp16.safetensors \
  --component-weights-paths.audio_vae /work/models/lilcheaty/vae/minimax_h3_audio_vae_fp32.safetensors \
  --num-gpus 1 --ulysses-degree 1 \
  --performance-mode manual \
  --text-encoder-cpu-offload true \
  --vae-cpu-offload true \
  --attention-backend sage_attn \
  --component-attention-backends text_encoder=torch_sdpa \
  --enable-torch-compile false \
  --warmup-mode off \
  --host 0.0.0.0 --port 30010 \
  --output-path /work/output
