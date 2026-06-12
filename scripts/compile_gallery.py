import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# Path definitions
ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "scripts" / "output"
GALLERY_DATA_PATH = ROOT_DIR / "src" / "data" / "gallery.json"

# Static mapping for high-quality fallback metadata
FALLBACK_METADATA = {
    "agentmemory": {
        "name": "AgentMemory",
        "description": "AI agent memory manager with local/cloud vector storage, key-value, and graph persistence.",
        "stars": 200,
        "language": "TypeScript"
    },
    "astro": {
        "name": "Astro",
        "description": "The web framework for content-driven websites.",
        "stars": 48000,
        "language": "TypeScript"
    },
    "axios": {
        "name": "Axios",
        "description": "Promise based HTTP client for the browser and node.js.",
        "stars": 105000,
        "language": "JavaScript"
    },
    "bitcoin": {
        "name": "Bitcoin Core",
        "description": "Bitcoin Core integration/staging tree.",
        "stars": 75000,
        "language": "C++"
    },
    "curl": {
        "name": "curl",
        "description": "A command line tool and library for transferring data with URLs.",
        "stars": 36000,
        "language": "C"
    },
    "flask": {
        "name": "Flask",
        "description": "The Python micro framework for building web applications.",
        "stars": 69000,
        "language": "Python"
    },
    "openclaw": {
        "name": "OpenClaw",
        "description": "Modern open-source implementation of Captain Claw (1997) platformer game.",
        "stars": 500,
        "language": "C++"
    },
    "powersploit": {
        "name": "PowerSploit",
        "description": "PowerSploit - A PowerShell Post-Exploitation Framework.",
        "stars": 11000,
        "language": "PowerShell"
    },
    "react": {
        "name": "React",
        "description": "A JavaScript library for building user interfaces.",
        "stars": 224000,
        "language": "JavaScript"
    },
    "react-native": {
        "name": "React Native",
        "description": "A framework for building native applications using React.",
        "stars": 118000,
        "language": "JavaScript"
    },
    "redis": {
        "name": "Redis",
        "description": "In-memory database that persists on disk.",
        "stars": 64000,
        "language": "C"
    },
    "tauri": {
        "name": "Tauri",
        "description": "Build smaller, faster, and more secure desktop applications with a web frontend.",
        "stars": 82000,
        "language": "Rust"
    }
}

def fetch_github_metadata(repo_path: str) -> tuple[str, int]:
    """Fetch description and stargazers_count from GitHub API with error handling."""
    url = f"https://api.github.com/repos/{repo_path}"
    headers = {"User-Agent": "Leit-Gallery-Compiler"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            description = data.get("description", "")
            stars = data.get("stargazers_count", 0)
            return description, stars
    except Exception as e:
        print(f"    ⚠ Could not fetch GitHub API for {repo_path}: {e}. Using fallback values.")
        return "", 0

def compile_gallery():
    if not OUTPUT_DIR.exists():
        print(f"Output directory not found at {OUTPUT_DIR}")
        return

    # Load existing gallery to preserve storage_base_url
    if GALLERY_DATA_PATH.exists():
        with open(GALLERY_DATA_PATH, "r") as f:
            gallery_data = json.load(f)
    else:
        gallery_data = {
            "storage_base_url": "https://saleitgallery.blob.core.windows.net/gallery",
            "entries": []
        }

    entries = []
    generated_at_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Read each folder under scripts/output/
    slugs = sorted([d.name for d in OUTPUT_DIR.iterdir() if d.is_dir()])
    print(f"Found {len(slugs)} repositories to compile.")

    for slug in slugs:
        print(f"Processing '{slug}'...")
        slug_dir = OUTPUT_DIR / slug
        profile_path = slug_dir / "profile.json"
        signature_path = slug_dir / "signature.json"

        if not profile_path.exists() or not signature_path.exists():
            print(f"  ⚠ Missing profile.json or signature.json for '{slug}', skipping.")
            continue

        with open(profile_path, "r") as f:
            profile = json.load(f)
        with open(signature_path, "r") as f:
            signature = json.load(f)

        # Extract repo path (e.g. owner/repo)
        repo_url = profile.get("repo_url", "")
        repo_path = repo_url.replace("https://github.com/", "").strip()
        if repo_path.endswith(".git"):
            repo_path = repo_path[:-4]

        fallback = FALLBACK_METADATA.get(slug, {
            "name": slug.title(),
            "description": f"Repository for {slug}",
            "stars": 100,
            "language": "JavaScript"
        })

        # Try fetching real-time description and stars from GitHub
        description, stars = fetch_github_metadata(repo_path)
        if not description:
            description = fallback["description"]
        if not stars:
            stars = fallback["stars"]

        # Determine dominant language from profile's language_summary
        language_summary = profile.get("language_summary", {})
        if language_summary:
            dominant_lang = max(language_summary, key=language_summary.get)
        else:
            dominant_lang = fallback["language"]

        # Combine key and scale (e.g. "D# major" or "D minor")
        scale = signature.get("scale", "")
        sig_key = signature.get("key", "")
        full_key = f"{sig_key} {scale}".strip()

        # Build metrics structure, rounding floats for clean serialization
        metrics_p = profile.get("architecture", {})
        metrics_q = profile.get("quality", {})
        
        entry = {
            "slug": slug,
            "name": fallback["name"],
            "repo": repo_path,
            "description": description,
            "language": dominant_lang,
            "stars": stars,
            "commit_sha": profile.get("commit_sha", "placeholder"),
            "generated_at": generated_at_time,
            "genre": signature.get("genre_profile", {}).get("primary", "synthwave"),
            "tempo": signature.get("tempo", 120),
            "key": full_key,
            "audio": {
                "wav": f"{slug}/signature.wav",
                "midi": f"{slug}/signature.mid",
                "gemini": f"{slug}/gemini.mp3"
            },
            "logo": f"/images/{slug}.svg",
            "metrics": {
                "complexity_score": round(metrics_q.get("complexity_score", 0.5), 2),
                "maintainability_score": round(metrics_q.get("maintainability_score", 0.5), 2),
                "coupling_score": round(metrics_p.get("coupling_score", 0.5), 4),
                "module_count": metrics_p.get("module_count", 0)
            }
        }
        
        entries.append(entry)

    # Save to src/data/gallery.json
    gallery_data["entries"] = entries
    with open(GALLERY_DATA_PATH, "w") as f:
        json.dump(gallery_data, f, indent=2)

    print(f"Successfully compiled {len(entries)} entries into {GALLERY_DATA_PATH}!")

if __name__ == "__main__":
    compile_gallery()
