"""Checks on what generate_names_with_llm returns. They call no model; tests/test_eval_checks.py tests them."""
import re

CAMEL_CASE = re.compile(r"[a-z][a-z0-9]*(?:[A-Z][a-z0-9]*)*")


def name_list_problems(names, count, context="", banned=()):
    """Return what is wrong with a result, as a list of strings; empty means it is good.

    Catches too few names only: the app cuts a longer list down to count before this sees it.
    """
    if names is None:
        return ["no names: the call failed or the answer was not a JSON list of strings"]
    problems = []
    if len(names) != count:
        problems.append(f"{len(names)} names, asked for {count}")
    seen = set()
    for name in names:
        key = name.strip().lower()
        if not key:
            problems.append("empty name")
        elif key in seen:
            problems.append(f"duplicate name: {name!r}")
        elif context and key == context.strip().lower():
            problems.append(f"the context echoed back as a name: {name!r}")
        elif len(name) > 40 or len(name.split()) > 6 or "\n" in name:
            problems.append(f"not a name (too long): {name!r}")
        elif re.fullmatch(r"name ?\d+", key):
            problems.append(f"the prompt's example echoed back: {name!r}")
        elif any(re.search(rf"\b{word}s?\b", key) for word in banned):
            problems.append(f"holds a banned word: {name!r}")
        seen.add(key)
    return problems


def not_camel_case(names):
    return [name for name in names if not CAMEL_CASE.fullmatch(name)]
