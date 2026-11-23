"""A pass/fail judge for what code can't check: do the names fit the context?"""
import json
import os

import requests

import app

# Not the model under test (openai/gpt-4o-mini), from the same provider so one key serves both.
JUDGE_MODEL = "openai/gpt-4.1-mini-2025-04-14"

QUESTION = """You grade a name generator. It was asked for names of the kind "{category}" with this context: "{context}".
It returned: {names}

Do the names fit the context?
Pass: most of the names have a clear link to the context (its subject, look, purpose or mood).
Fail: most of the names would suit any request of this kind and show no link to the context, or they name a different kind of thing.

Answer with only a JSON object, the reason first: {{"reason": "<one sentence>", "verdict": "pass" or "fail"}}"""


def parse_verdict(reply):
    """Return (passed, reason). Anything but a clear pass counts as a fail."""
    try:
        answer = json.loads(reply.strip().removeprefix("```json").removesuffix("```"))
        return answer["verdict"] == "pass", str(answer.get("reason", ""))
    except (ValueError, KeyError, TypeError, AttributeError):
        return False, f"no clear verdict: {reply!r}"


def names_fit_context(category, context, names):
    response = requests.post(
        app.OPENROUTER_BASE_URL,
        headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
        json={
            "model": JUDGE_MODEL,
            "messages": [{"role": "user", "content": QUESTION.format(category=category, context=context, names=json.dumps(names))}],
            "temperature": 0,
        },
        timeout=30,
    )
    response.raise_for_status()
    return parse_verdict(response.json()["choices"][0]["message"]["content"])
