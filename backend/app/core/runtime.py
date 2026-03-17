from __future__ import annotations

from functools import lru_cache
import subprocess


@lru_cache
def get_runtime_info() -> dict[str, bool | str]:
    gpu_name = ""
    nvidia_smi_available = False
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            gpu_name = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
            nvidia_smi_available = bool(gpu_name)
    except Exception:
        nvidia_smi_available = False

    try:
        import torch

        cuda_available = bool(torch.cuda.is_available())
        return {
            "torch_available": True,
            "cuda_available": cuda_available,
            "device": "cuda" if cuda_available else "cpu",
            "nvidia_smi_available": nvidia_smi_available,
            "gpu_name": gpu_name,
            "torch_version": getattr(torch, "__version__", ""),
        }
    except Exception:
        return {
            "torch_available": False,
            "cuda_available": False,
            "device": "cpu",
            "nvidia_smi_available": nvidia_smi_available,
            "gpu_name": gpu_name,
            "torch_version": "",
        }
