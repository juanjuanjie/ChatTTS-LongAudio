import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / "venv"
LOG_DIR = ROOT / "logs"
REQ_FILE = ROOT / "requirements.txt"
ENV_EXAMPLE = ROOT / ".env.example"
ENV_FILE = ROOT / ".env"
STAMP_FILE = VENV_DIR / ".bootstrap_stamp"
APP_FILE = ROOT / "app.py"


def run(cmd, *, check=True, env=None):
    print("+ " + " ".join(str(part) for part in cmd), flush=True)
    return subprocess.run([str(part) for part in cmd], cwd=ROOT, check=check, env=env)


def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def ensure_supported_python():
    major, minor = sys.version_info[:2]
    if (major, minor) in {(3, 10), (3, 11)}:
        return

    fallback = find_supported_python()
    if fallback:
        print(
            f"Current Python is {major}.{minor}; switching to {fallback}",
            flush=True,
        )
        raise SystemExit(subprocess.call([str(fallback), str(Path(__file__).resolve())], cwd=ROOT))

    raise SystemExit(
        "This project needs Python 3.10 or 3.11. "
        f"Current Python is {major}.{minor}. "
        "Please install Python 3.10/3.11, then double-click _run_app.bat again."
    )


def find_supported_python() -> Path | None:
    candidates: list[Path] = []

    py_launcher = shutil.which("py")
    if py_launcher:
        try:
            result = subprocess.run(
                [py_launcher, "-0p"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=10,
            )
            for line in result.stdout.splitlines():
                if "3.10" not in line and "3.11" not in line:
                    continue
                parts = line.strip().split()
                if parts:
                    candidates.append(Path(parts[-1]))
        except Exception:
            pass

    for name in ("python3.11", "python3.10"):
        exe = shutil.which(name)
        if exe:
            candidates.append(Path(exe))

    current = Path(sys.executable).resolve()
    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            resolved = candidate.resolve()
        except OSError:
            resolved = candidate
        if resolved == current:
            continue
        check = subprocess.run(
            [str(candidate), "-c", "import sys; raise SystemExit(0 if sys.version_info[:2] in {(3,10),(3,11)} else 1)"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if check.returncode == 0:
            return candidate

    return None


def has_nvidia_gpu() -> bool:
    exe = shutil.which("nvidia-smi")
    if not exe:
        return False
    try:
        result = subprocess.run([exe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8)
        return result.returncode == 0
    except Exception:
        return False


def torch_install_command(py: Path) -> list[str]:
    mode = os.environ.get("CHATTTS_TORCH", "auto").strip().lower()
    if mode == "auto":
        mode = "cu118" if has_nvidia_gpu() else "cpu"

    if mode in {"gpu", "cuda", "cu118"}:
        print("PyTorch mode: CUDA 11.8 wheel", flush=True)
        return [
            str(py),
            "-m",
            "pip",
            "install",
            "torch==2.3.1+cu118",
            "torchaudio==2.3.1+cu118",
            "--index-url",
            "https://download.pytorch.org/whl/cu118",
        ]

    print("PyTorch mode: CPU wheel", flush=True)
    return [
        str(py),
        "-m",
        "pip",
        "install",
        "torch==2.3.1+cpu",
        "torchaudio==2.3.1+cpu",
        "--index-url",
        "https://download.pytorch.org/whl/cpu",
    ]


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def desired_stamp() -> str:
    torch_mode = os.environ.get("CHATTTS_TORCH", "auto").strip().lower()
    gpu_state = "gpu" if torch_mode == "auto" and has_nvidia_gpu() else "nogpu"
    return "|".join(
        [
            f"python={sys.version_info.major}.{sys.version_info.minor}",
            f"requirements={file_hash(REQ_FILE)}",
            f"torch={torch_mode}",
            f"gpu={gpu_state}",
        ]
    )


def package_import_ok(py: Path, module: str) -> bool:
    result = subprocess.run(
        [str(py), "-c", f"import {module}"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def python_version_ok(py: Path) -> bool:
    result = subprocess.run(
        [
            str(py),
            "-c",
            "import sys; raise SystemExit(0 if sys.version_info[:2] in {(3,10),(3,11)} else 1)",
        ],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def ensure_venv():
    py = venv_python()
    if py.exists() and python_version_ok(py):
        return py
    if VENV_DIR.exists():
        print("Rebuilding invalid virtual environment: venv", flush=True)
        shutil.rmtree(VENV_DIR)

    print("Creating virtual environment: venv", flush=True)
    run([sys.executable, "-m", "venv", str(VENV_DIR)])
    return py


def ensure_dependencies(py: Path):
    stamp = desired_stamp()
    installed = STAMP_FILE.read_text(encoding="utf-8").strip() if STAMP_FILE.exists() else ""
    if installed == stamp and package_import_ok(py, "torch") and package_import_ok(py, "flask"):
        print("Dependencies already installed.", flush=True)
        return

    print("Installing dependencies. This may take a while on first run.", flush=True)
    run([py, "-m", "pip", "install", "--upgrade", "pip"])
    if not package_import_ok(py, "torch") or not package_import_ok(py, "torchaudio"):
        run(torch_install_command(py))
    run([py, "-m", "pip", "install", "-r", REQ_FILE])

    if not package_import_ok(py, "torch"):
        raise SystemExit("PyTorch installation failed. Please check your network and disk space.")

    STAMP_FILE.write_text(stamp, encoding="utf-8")


def ensure_env_file():
    if not ENV_FILE.exists() and ENV_EXAMPLE.exists():
        shutil.copyfile(ENV_EXAMPLE, ENV_FILE)
        print("Created .env from .env.example", flush=True)


def main():
    LOG_DIR.mkdir(exist_ok=True)
    ensure_supported_python()
    ensure_env_file()
    py = ensure_venv()
    ensure_dependencies(py)

    print("", flush=True)
    print("Starting ChatTTS LongAudio...", flush=True)
    print("Open this URL after startup: http://localhost:9966", flush=True)
    print("", flush=True)
    raise SystemExit(run([py, "-u", APP_FILE], check=False).returncode)


if __name__ == "__main__":
    main()
