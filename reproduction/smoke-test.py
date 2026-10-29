"""CPU-only checks. These do not validate CUDA execution or video quality."""
import importlib
import importlib.metadata as metadata
import json
from pathlib import Path
import subprocess

import torch
import sageattention

for name in ("sageattention._fused", "sageattention._qattn_sm80", "sageattention._qattn_sm89"):
    extension = importlib.import_module(name)
    cubins = subprocess.check_output(["cuobjdump", "--list-elf", extension.__file__], text=True)
    assert "sm_120" in cubins, f"SM120 cubin missing in {name}: {cubins}"
assert callable(sageattention.sageattn)
assert metadata.version("sageattention") == "2.2.0"
assert metadata.version("comfy-kitchen") == "0.2.40"
root = Path(importlib.util.find_spec("sglang").origin).parent
runtime = root / "multimodal_gen" / "runtime"
assert runtime.is_dir(), f"SGLang diffusion runtime missing in {root}"
assert any(runtime.rglob("*minimax_h3*")), "MiniMax H3 implementation missing"
assert any(runtime.rglob("sage_attn.py")), "SageAttention backend missing"
print(json.dumps({
    "torch": torch.__version__, "torch_cuda": torch.version.cuda,
    "sglang": metadata.version("sglang"),
    "sageattention": metadata.version("sageattention"),
    "comfy_kitchen": metadata.version("comfy-kitchen"),
    "cuda_available": torch.cuda.is_available(),
    "validation": "CPU import and compiled-extension checks only",
}, indent=2))
