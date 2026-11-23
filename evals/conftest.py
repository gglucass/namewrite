"""Loads the OpenRouter key the way `flask run` does (from .env), before app.py reads it at import."""
import subprocess
from pathlib import Path

from dotenv import load_dotenv

root = Path(__file__).resolve().parent.parent
env = root / ".env"
if not env.exists():
    # In a git worktree the ignored .env exists only in the main checkout.
    common = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=root, capture_output=True, text=True,
    ).stdout.strip()
    env = Path(common).parent / ".env"
load_dotenv(env)
