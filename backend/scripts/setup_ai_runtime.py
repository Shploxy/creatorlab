from __future__ import annotations

import argparse
import subprocess
import sys


CPU_INDEX = "https://download.pytorch.org/whl/cpu"
CUDA_INDEX = "https://download.pytorch.org/whl/cu128"


def detect_nvidia_gpu() -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return False, ""
    if result.returncode != 0 or not result.stdout.strip():
        return False, ""
    return True, result.stdout.strip().splitlines()[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="Configure CreatorLab AI runtime for Windows.")
    parser.add_argument("--apply", action="store_true", help="Run the pip install commands instead of printing them.")
    args = parser.parse_args()

    has_gpu, gpu_name = detect_nvidia_gpu()
    python_exe = sys.executable
    index_url = CUDA_INDEX if has_gpu else CPU_INDEX
    onnx_package = "onnxruntime-gpu" if has_gpu else "onnxruntime"
    commands = [
        [python_exe, "-m", "pip", "install", "--upgrade", "pip"],
        [python_exe, "-m", "pip", "install", "torch", "torchvision", "--index-url", index_url],
        [python_exe, "-m", "pip", "install", "basicsr", "realesrgan", onnx_package],
    ]

    print(f"Detected GPU: {gpu_name if has_gpu else 'none'}")
    print(f"Selected Torch index: {index_url}")

    if not args.apply:
        print("Planned commands:")
        for command in commands:
            print(" ", " ".join(command))
        return

    for command in commands:
        subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
