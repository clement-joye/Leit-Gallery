"""
Gallery seeding script.

Runs the Leit pipeline on each curated repository and outputs:
  - signature JSON (committed to leit-gallery repo)
  - WAV file (uploaded to Azure Blob Storage)
  - MIDI file (uploaded to Azure Blob Storage)

Prerequisites:
  - Leit core must be installed and working locally
  - Azure Storage credentials in environment variables
  - Repos must be accessible (public GitHub repos)

Usage:
    python scripts/seed_gallery.py [--repos react,django,flask] [--upload]

Environment variables:
    AZURE_STORAGE_CONNECTION_STRING - Azure Blob Storage connection string
    AZURE_STORAGE_CONTAINER - Container name (default: "gallery")
    LEIT_CORE_PATH - Path to Leit main repository (default: ../Leit)
"""

import argparse
import json
import os
import shlex
import time
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        """Minimal fallback loader for a local .env file."""
        env_path = Path(__file__).resolve().parent.parent / ".env"
        if not env_path.exists():
            return False

        for raw_line in env_path.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'\"")
            if key and key not in os.environ:
                os.environ[key] = value
        return True

load_dotenv()

print(os.environ["AZURE_STORAGE_CONNECTION_STRING"])

GALLERY_DATA = Path(__file__).parent.parent / "src" / "data" / "gallery.json"
OUTPUT_ROOT = Path(__file__).parent / "output"
LEIT_CORE_PATH = Path("/home/cj/Documents/repos/Leit/")
LEIT_PYTHON = LEIT_CORE_PATH / ".venv" / "bin" / "python"

# Repos to generate signatures for (must match gallery.json slugs)
CURATED_REPOS = {
    "agentmemory": "https://github.com/rohitg00/agentmemory",
    "astro": "https://github.com/withastro/astro",
    "axios": "https://github.com/axios/axios",
    "bitcoin": "https://github.com/bitcoin/bitcoin",
    "curl": "https://github.com/curl/curl",
    "django": "https://github.com/django/django",
    "fastapi": "https://github.com/fastapi/fastapi",
    "flask": "https://github.com/pallets/flask",
    "gin": "https://github.com/gin-gonic/gin",
    "next-js": "https://github.com/vercel/next.js",
    "pytorch": "https://github.com/pytorch/pytorch",
    "openclaw": "https://github.com/openclaw/openclaw",
    "react": "https://github.com/facebook/react",
    "react-native": "https://github.com/react/react-native",
    "redis": "https://github.com/redis/redis",
    "tauri": "https://github.com/tauri-apps/tauri"
    "vscode": "https://github.com/microsoft/vscode",
}


def _get_leit_python() -> str:
    """Prefer the Leit repo virtualenv; fall back to the current interpreter."""
    return str(LEIT_PYTHON) if LEIT_PYTHON.exists() else sys.executable


def _format_duration(start_time: float) -> str:
    elapsed = time.monotonic() - start_time
    return f"{elapsed:.1f}s"


def _run_streaming_command(cmd: list[str], *, cwd: Path | None = None, prefix: str = "") -> subprocess.CompletedProcess[str]:
    """Run a command while streaming stdout/stderr line by line."""
    label = f"{prefix} " if prefix else ""
    print(f"  {label}Running: {shlex.join(cmd)}")
    start = time.monotonic()
    process = subprocess.Popen(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None

    output_lines: list[str] = []
    stop_heartbeat = threading.Event()

    def _heartbeat() -> None:
        while not stop_heartbeat.wait(30):
            print(f"  {label}Still running after {_format_duration(start)}...")

    heartbeat_thread = threading.Thread(target=_heartbeat, daemon=True)
    heartbeat_thread.start()
    for raw_line in process.stdout:
        line = raw_line.rstrip("\n")
        output_lines.append(raw_line)
        print(f"  {label}{line}")

    returncode = process.wait()
    stop_heartbeat.set()
    heartbeat_thread.join(timeout=1)
    duration = _format_duration(start)
    print(f"  {label}Finished in {duration} (exit code {returncode})")
    return subprocess.CompletedProcess(cmd, returncode, "".join(output_lines), None)


def _clone_repo(repo_url: str, clone_dir: Path) -> None:
    """Clone a repository shallowly for local analysis."""
    clone_cmd = ["git", "clone", "--depth", "1", "--progress", "--", repo_url, str(clone_dir)]
    result = _run_streaming_command(clone_cmd, prefix="[clone]")
    if result.returncode != 0:
        raise RuntimeError((result.stdout or "").strip() or "git clone failed")


def run_leit_analysis(repo_url: str, output_dir: Path) -> dict:
    """Run Leit CLI on a repository and return the result."""
    with tempfile.TemporaryDirectory(prefix="leit-gallery-") as tmpdir:
        repo_path = Path(tmpdir) / "repo"
        _clone_repo(repo_url, repo_path)

        cmd = [
            _get_leit_python(),
            str(LEIT_CORE_PATH / "cli" / "main.py"),
            "analyze",
            str(repo_path),
            "--output",
            str(output_dir),
            "--repo-url",
            repo_url,
        ]
        result = _run_streaming_command(cmd, cwd=LEIT_CORE_PATH, prefix="[analysis]")

        if result.returncode != 0:
            print("  ✗ Analysis failed")
            return None

        # Read the output JSON
        output_files = list(output_dir.glob("*.json"))
        if not output_files:
            print(f"  ✗ No output JSON found")
            return None

        with open(output_files[0], "r") as f:
            return json.load(f)


def upload_to_azure(local_path: Path, blob_name: str):
    """Upload a file to Azure Blob Storage."""
    try:
        from azure.storage.blob import BlobServiceClient

        connection_string = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
        container_name = os.environ.get("AZURE_STORAGE_CONTAINER", "gallery")

        blob_service = BlobServiceClient.from_connection_string(connection_string)
        container = blob_service.get_container_client(container_name)

        with open(local_path, "rb") as data:
            container.upload_blob(name=blob_name, data=data, overwrite=True)

        print(f"  ✓ Uploaded {blob_name}")
    except ImportError:
        print("  ✗ azure-storage-blob not installed. Run: pip install azure-storage-blob")
        sys.exit(1)
    except KeyError:
        print("  ✗ AZURE_STORAGE_CONNECTION_STRING not set")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Seed the Leit Gallery with pre-computed signatures")
    parser.add_argument("--repos", type=str, help="Comma-separated list of slugs to process (default: all)")
    parser.add_argument("--upload", action="store_true", help="Upload audio files to Azure Blob Storage")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done without executing")
    args = parser.parse_args()

    slugs = args.repos.split(",") if args.repos else list(CURATED_REPOS.keys())

    print(f"Leit Gallery Seeder")
    print(f"  Core path: {LEIT_CORE_PATH}")
    print(f"  Repos to process: {len(slugs)}")
    print()

    for slug in slugs:
        if slug not in CURATED_REPOS:
            print(f"  ⚠ Unknown slug: {slug}, skipping")
            continue

        repo_url = CURATED_REPOS[slug]
        print(f"[{slug}] {repo_url}")

        if args.dry_run:
            print(f"  (dry run) Would analyze and generate audio")
            continue

        output_dir = OUTPUT_ROOT / slug
        output_dir.mkdir(parents=True, exist_ok=True)

        # Run analysis
        started = time.monotonic()
        result = run_leit_analysis(repo_url, output_dir)
        if not result:
            continue

        # Upload audio files if requested
        if args.upload:
            wav_path = output_dir / "signature.wav"
            midi_path = output_dir / "signature.mid"
            gemini_path = output_dir / "gemini.mp3"

            if wav_path.exists():
                upload_to_azure(wav_path, f"{slug}/signature.wav")
            if midi_path.exists():
                upload_to_azure(midi_path, f"{slug}/signature.mid")
            if gemini_path.exists():
                upload_to_azure(gemini_path, f"{slug}/gemini.mp3")

        print(f"  ✓ Done in {_format_duration(started)}")
        print()

    print("Gallery seeding complete.")


if __name__ == "__main__":
    main()
