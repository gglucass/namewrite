"""Shared by the generate-names evals: runs the production call and checks its reply."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import requests

ROOT = Path(__file__).resolve().parent.parent
# Not the model under test (openai/gpt-4o-mini); same provider, so the same key pays for it.
# A dated snapshot this OpenRouter account can reach: its data policy excludes openai/gpt-4o-2024-11-20.
JUDGE_MODEL = "openai/gpt-4o-2024-08-06"


def _load_env():
    """The app reads OPENROUTER_API_KEY from the environment; eval runs also take it from a git-ignored .env."""
    # In a git worktree the .env is only in the main checkout, next to the shared .git folder.
    shared = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=ROOT, capture_output=True, text=True,
    ).stdout.strip()
    for folder in [ROOT] + ([Path(shared).parent] if shared else []):
        env = folder / ".env"
        if env.is_file():
            # shortcut: reads plain KEY=VALUE lines only, switch to python-dotenv if the file needs more
            for line in env.read_text().splitlines():
                key, sep, value = line.strip().removeprefix("export ").partition("=")
                if sep and not key.startswith("#"):
                    os.environ.setdefault(key.strip(), value.strip().strip("'\""))
            return


_load_env()
sys.path.insert(0, str(ROOT))
import app  # noqa: E402  (after the key is in the environment: app reads it at import)


def record(name, value):
    """Stands in for pytest's record_property, which conftest.py puts here during a test."""


def ask(category, context, count):
    """Runs the production call. Returns (the names the app got, the model's raw reply)."""
    assert app.OPENROUTER_API_KEY, "OPENROUTER_API_KEY is not set: export it, or add it to a .env in the repo root"
    raw = []
    post = requests.post

    def spy(*args, **kwargs):
        response = post(*args, **kwargs)
        try:
            raw.append(response.json()["choices"][0]["message"]["content"])
        except Exception:
            raw.append(response.text)
        return response

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(requests, "post", spy)
        names = app.generate_names_with_llm(category, context, count)
    # evalship's report shows what the model got and said, before and after a change.
    record("input", json.dumps({"category": category, "context": context, "count": count}))
    record("output", raw[0] if raw else "")
    return names, raw[0] if raw else None


def problems(names, raw, count):
    """What is wrong with a reply, as a list of lines; empty when it is right."""
    if names is None:
        return [f"the app could not use the reply, so its users get fallback names: {raw!r}"]
    found = []
    # The app cuts the list to count, so only the raw reply shows the model sent too many.
    replied = len(json.loads(raw))
    if replied != count:
        found.append(f"asked for {count} names, the reply has {replied}")
    for name in names:
        # Markdown, numbering or "Name: tagline" is formatting the page would show as part of the name.
        if not name.strip() or len(name.split()) > 5 or len(name) > 60 or re.search(r"[*:#`\n]|^\s*\d+[.)]", name):
            found.append(f"not a name: {name!r}")
    lowered = [name.strip().lower() for name in names]
    doubles = sorted({name for name in lowered if lowered.count(name) > 1})
    if doubles:
        found.append(f"duplicate names: {doubles}")
    return found


def all_camel_case(names):
    """Every name is camelCase, and at least one has a capital: five one-word names dodge the rule."""
    return all(re.fullmatch(r"[a-z][a-z0-9]*([A-Z][a-z0-9]*)*", name) for name in names) and any(
        re.search("[A-Z]", name) for name in names
    )


def verdict(reply):
    """True only for a reply that ends in VERDICT: PASS; anything unclear fails."""
    # The judge sometimes ends the line with a period or wraps it in bold.
    end = re.search(r"VERDICT: (PASS|FAIL)[\s.*]*$", reply or "")
    return bool(end) and end.group(1) == "PASS"


def judge(question, passes, fails, answer):
    """Asks another model one pass/fail question. Returns (passed, the judge's reply)."""
    response = requests.post(
        app.OPENROUTER_BASE_URL,
        headers={"Authorization": f"Bearer {app.OPENROUTER_API_KEY}"},
        json={
            "model": JUDGE_MODEL,
            "temperature": 0,
            "messages": [{"role": "user", "content": (
                f"{question}\n\nPass: {passes}\nFail: {fails}\n\nAnswer to judge:\n{answer}\n\n"
                "Give your reason in one or two sentences. "
                "Then end with a last line that is exactly VERDICT: PASS or VERDICT: FAIL."
            )}],
        },
        timeout=60,
    )
    body = response.json()
    assert "choices" in body, f"the judge model gave no answer: {body.get('error')}"
    reply = body["choices"][0]["message"]["content"]
    return verdict(reply), reply


def fits_context(kind, context, raw):
    """Judges whether the names are about what the user asked for. Returns (passed, the judge's reply)."""
    return judge(
        f"A user asked for {kind} with this context: {context!r}. Do the names fit that context?",
        "at least half of the names call the context to mind, by their meaning or by what they describe. "
        "A list of one name passes when that name does.",
        "most of the names would suit any request for such names, or the reply is not a list of names.",
        raw,
    )
