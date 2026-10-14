"""Truth table for US / non-US / unknown location classification."""

import pytest

from scraper.location import classify, is_us


@pytest.mark.parametrize(
    "location",
    [
        "US, Remote",
        "Remote - US",
        "Remote, United States",
        "San Francisco, CA",
        "New York, NY",
        "Washington, D.C.",
        "Austin, TX / Remote",
        "Remote (US)",
        "California",
        "Columbia, MD",
        "San Francisco, CA / London",   # also hires in US -> kept
        "Nationwide",
        "Fort Meade, MD, USA",
    ],
)
def test_us_locations(location):
    assert classify(location) is True
    assert is_us(location) is True


@pytest.mark.parametrize(
    "location",
    [
        "London, UK",
        "Remote - EMEA",
        "Bengaluru, India",
        "Toronto, Canada",
        "Tel Aviv, Israel",
        "Berlin, Germany",
        "Sydney, Australia",
        "Remote - Europe",
        "Singapore",
        "Dublin, Ireland",
    ],
)
def test_non_us_locations(location):
    assert classify(location) is False
    assert is_us(location) is False


@pytest.mark.parametrize("location", ["", None, "Remote", "Anywhere"])
def test_unknown_locations(location):
    assert classify(location) is None
    assert is_us(location, include_unknown=True) is True
    assert is_us(location, include_unknown=False) is False


def test_plus_does_not_false_match_us_token():
    # "us" inside "plus" must not count as a US signal.
    assert classify("Surplus role, Berlin") is False
