"""The eval checks on made-up results: right ones pass, wrong ones fail. Calls no model."""
from evals.checks import name_list_problems, not_camel_case
from evals.judge import parse_verdict


def test_right_answers_pass():
    assert name_list_problems(["Aurora", "Nexus", "Spark"], 3) == []
    assert name_list_problems(["Mr. Whiskers", "Sir Purrs-a-Lot"], 2, "orange cat") == []
    assert name_list_problems(["Crumb"], 1, "a bakery") == []
    assert name_list_problems(["Sir Purrs a Lot Jr", "Chelsea", "Seamus"], 3, banned=("sea",)) == []
    assert not_camel_case(["sessionCache", "cache", "userId2", "httpURLCache"]) == []


def test_wrong_answers_fail():
    assert name_list_problems(None, 3)  # empty, refusal or unparseable answer
    assert name_list_problems([], 3)
    assert name_list_problems(["Aurora", "Nexus"], 3)  # near miss: one short
    assert name_list_problems(["Aurora", "aurora ", "Nexus"], 3)  # duplicate
    assert name_list_problems(["Aurora", " ", "Nexus"], 3)  # empty name
    assert name_list_problems(["a bakery"], 1, "A Bakery")  # the input echoed
    assert name_list_problems(["The sea is wide and deep and blue"], 1)  # a poem line
    assert name_list_problems(["Sorry, I can't help with that request."], 1)  # a refusal as a name
    assert name_list_problems(["Name1", "Name2", "Name3"], 3)  # the prompt's own example
    assert name_list_problems(["The sea is wide", "Waves roll on"], 2, banned=("sea", "wave"))  # short poem lines
    assert not_camel_case(["SessionCache"]) == ["SessionCache"]
    assert not_camel_case(["session_cache", "session cache", "2cache", ""]) == ["session_cache", "session cache", "2cache", ""]


def test_judge_verdicts():
    assert parse_verdict('{"reason": "All names evoke orange fur.", "verdict": "pass"}')[0]
    assert parse_verdict('```json\n{"reason": "Fits.", "verdict": "pass"}\n```')[0]
    assert not parse_verdict('{"reason": "Generic names.", "verdict": "fail"}')[0]
    assert not parse_verdict("These names do not pass.")[0]  # no clear verdict
    assert not parse_verdict('{"verdict": "pass or fail"}')[0]
    assert not parse_verdict('["pass"]')[0]
    assert not parse_verdict("")[0]
