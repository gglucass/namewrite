"""Tests of the eval checks on made-up replies. They call no model, so plain `pytest` runs them."""

import json

import pytest
import requests

import checks
from checks import all_camel_case, ask, problems, verdict

FIVE = ["NoteNest", "StudyLoop", "PageMint", "ClassCue", "InkTrail"]


class Reply:
    """What requests.post returns for a made-up model reply."""

    status_code = 200

    def __init__(self, content):
        self.text = content

    def json(self):
        return {"choices": [{"message": {"content": self.text}}]}


def check(monkeypatch, reply):
    """Puts a made-up reply through the app's own parsing, then through the checks."""
    monkeypatch.setattr(checks.app, "OPENROUTER_API_KEY", "made-up")
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: Reply(reply))
    return problems(*ask("project", "a note-taking app for students", 5), 5)


@pytest.mark.parametrize("reply", [
    json.dumps(FIVE),
    ' [\n  "Note Nest",\n  "Study Loop",\n  "Page Mint",\n  "Class Cue",\n  "Ink Trail"\n]\n',
    json.dumps(["Aurora", "Nexus Labs", "Spark", "Horizon Notes", "Pulse"]),
])
def test_right_replies_pass(monkeypatch, reply):
    assert check(monkeypatch, reply) == []


@pytest.mark.parametrize("reply", [
    "",
    "a note-taking app for students",
    "I'm sorry, I can't help with that.",
    json.dumps(FIVE[:4]),
    json.dumps(FIVE + ["DeskLamp"]),
    "```json\n" + json.dumps(FIVE) + "\n```",
    "Here are 5 names: " + json.dumps(FIVE),
    json.dumps({"names": FIVE}),
    "[1, 2, 3, 4, 5]",
    "[]",
    json.dumps(FIVE[:4] + [" "]),
    json.dumps(FIVE[:4] + ["notenest"]),
    json.dumps(FIVE[:4] + ["A note-taking app that students open every day"]),
    json.dumps(["a note-taking app for students"] * 5),
    json.dumps(FIVE[:4] + ["5. InkTrail"]),
    json.dumps(FIVE[:4] + ["**InkTrail**"]),
    json.dumps(FIVE[:4] + ["InkTrail: notes that stick"]),
], ids=[
    "empty", "input echoed", "refusal", "one name short", "one name too many", "code fence",
    "text around it", "object", "numbers", "empty array", "blank name", "duplicate", "sentence",
    "input echoed five times", "numbered", "markdown", "tagline",
])
def test_wrong_replies_fail(monkeypatch, reply):
    assert check(monkeypatch, reply) != []


def test_no_reply_fails(monkeypatch):
    def down(*args, **kwargs):
        raise requests.exceptions.ConnectionError("made-up outage")

    monkeypatch.setattr(checks.app, "OPENROUTER_API_KEY", "made-up")
    monkeypatch.setattr(requests, "post", down)
    assert problems(*ask("project", "fast", 5), 5) != []


def test_missing_key_fails_naming_the_variable(monkeypatch):
    monkeypatch.setattr(checks.app, "OPENROUTER_API_KEY", None)
    with pytest.raises(AssertionError, match="OPENROUTER_API_KEY"):
        ask("project", "fast", 5)


def test_camel_case():
    assert all_camel_case(["cartTotal", "total", "priceAfterDiscounts", "userID", "item2Price"])
    for wrong in ["CartTotal", "cart_total", "cart total", "cart-total", "", "2ndPrice"]:
        assert not all_camel_case(["cartTotal", wrong]), wrong
    assert not all_camel_case(["total", "price", "cart"])


def test_verdict():
    assert verdict("Four of the names mention the sun.\nVERDICT: PASS")
    assert verdict("Four names fit.\n\n**VERDICT: PASS**\n")
    assert verdict("Each could stand alone as a project name. VERDICT: PASS.")
    assert not any(verdict(reply) for reply in [
        "Only one name fits.\nVERDICT: FAIL",
        "",
        None,
        "The names do not pass.",
        "VERDICT: PASS\nOn reflection, only two fit.\nVERDICT: FAIL",
        "It could be VERDICT: PASS or VERDICT: FAIL.",
    ])
