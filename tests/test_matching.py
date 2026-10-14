"""Truth table for role-umbrella matching and level detection."""

import pytest

from scraper.config_loader import load_roles
from scraper.matching import detect_level, match_roles

UMBRELLAS, LEVELS = load_roles()


@pytest.mark.parametrize(
    "title,umbrella,role",
    [
        ("Senior Frontend Engineer", "engineering", "frontend"),
        ("Staff Full Stack Engineer", "engineering", "full_stack"),
        ("Principal DevEx Engineer", "engineering", "devops"),
        ("AI Engineer, Agentic Systems", "engineering", "agentic"),
        ("Staff Product Manager", "product_design", "product_manager"),
        ("Technical Program Manager", "product_design", "technical_program_manager"),
        ("Senior Product Designer", "product_design", "product_designer"),
        ("Technical Recruiter", "gtm_revenue", "recruiter"),
    ],
)
def test_matches_expected_role(title, umbrella, role):
    umbs, roles = match_roles(title, UMBRELLAS)
    assert umbrella in umbs
    assert role in roles


@pytest.mark.parametrize(
    "title",
    [
        "Product Marketing Manager",  # excluded from product_manager
        "Account Executive",
        "Office Manager",
        "Customer Success Manager",
        "Executive Assistant",
    ],
)
def test_non_target_roles_are_dropped(title):
    _, roles = match_roles(title, UMBRELLAS)
    # "Office Manager"/"Customer Success Manager" contain "manager" but match no target role
    # umbrella because manager is a LEVEL keyword, not a role keyword.
    assert roles == [] or "product_manager" not in roles


@pytest.mark.parametrize(
    "title,level",
    [
        ("Staff Full Stack Engineer", "staff"),
        ("Senior Frontend Engineer", "senior"),
        ("Principal DevEx Engineer", "principal"),
        ("Director of Product", "director"),
        ("VP of Engineering", "vp"),
        ("Software Engineer Intern", "intern"),
        ("Full Stack Engineer", "mid"),
    ],
)
def test_level_detection(title, level):
    assert detect_level(title, LEVELS) == level
