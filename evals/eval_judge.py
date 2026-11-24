"""Checks the judge against lists labeled right or wrong. Run it after a change to the judge's model or questions:

    .venv/bin/python -m pytest evals/eval_judge.py

It calls the judge model only, so it says nothing about the product: keep it out of the results sent to evalship.
"""

import json

import pytest

from checks import are_names, fits_context

SOLAR = ("company names", "solar panels for homes")
CART = ("variable names", "the total price of a shopping cart after discounts")
BAKERY = ("a company name", "a bakery that delivers by bike")
PLAIN = ["Aurora", "Nexus", "Spark", "Horizon", "Pulse"]

FITS = {
    "solar names": (SOLAR, ["SunRoof Energy", "HomeBeam", "BrightHaus Solar", "RayNest", "Voltly"], True),
    "any company for solar": (SOLAR, PLAIN, False),
    "cart variables": (CART, ["cartTotal", "discountedPrice", "finalCartPrice", "totalAfterDiscounts", "netCartAmount"], True),
    "any variable for cart": (CART, ["dataProcessor", "resultHandler", "configManager", "eventDispatcher", "stateController"], False),
    "one bakery name": (BAKERY, ["BicycleBakery"], True),
    "one unrelated name": (BAKERY, ["TechFlow"], False),
    "ten kitten names": (
        ("pet names", "a litter of ten black kittens"),
        ["Shadow", "Midnight", "Onyx", "Coal", "Raven", "Ink", "Pepper", "Jet", "Ebony", "Soot"],
        True,
    ),
    "refusal": (("software project names", "fast"), "I'm sorry, I can't help with that.", False),
}

NAMES = {
    "plain project names": (PLAIN, True),
    "sea names with a poetic one": (["SeaVerse", "TideFlow", "Ode to the Sea", "DeepBlue", "WaveCraft"], True),
    "poem in five lines": (["Waves roll in", "Salt and foam", "Deep blue calls", "Tides turn slow", "Sea sings on"], False),
    "refusal cut in five": (["Sorry", "I cannot", "write poems", "only names", "here"], False),
}


@pytest.mark.parametrize("request_, reply, right", FITS.values(), ids=FITS.keys())
def test_fits_context(request_, reply, right):
    passed, reason = fits_context(*request_, reply if isinstance(reply, str) else json.dumps(reply))
    assert passed == right, reason


@pytest.mark.parametrize("reply, right", NAMES.values(), ids=NAMES.keys())
def test_are_names(reply, right):
    passed, reason = are_names(json.dumps(reply))
    assert passed == right, reason
