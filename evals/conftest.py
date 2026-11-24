import pytest

import checks


@pytest.fixture(autouse=True)
def record_calls(record_property, monkeypatch):
    """Puts each case's input and the model's reply in the results file."""
    monkeypatch.setattr(checks, "record", record_property)
