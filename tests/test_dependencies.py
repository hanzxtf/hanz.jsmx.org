"""The pinned production requirements must match the locked environment."""

import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
REQUIREMENTS = BASE_DIR / "requirements.txt"
LOCK = BASE_DIR / "uv.lock"

LOCK_PACKAGE = re.compile(r'\[\[package\]\]\nname = "([^"]+)"\nversion = "([^"]+)"')
REQUIREMENT = re.compile(r"^([A-Za-z0-9._-]+)==([^\s;]+)")


def normalise(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def test_requirements_match_the_lock():
    locked = {
        normalise(name): version
        for name, version in LOCK_PACKAGE.findall(LOCK.read_text())
    }
    pinned = [
        match.groups()
        for line in REQUIREMENTS.read_text().splitlines()
        if (match := REQUIREMENT.match(line))
    ]
    assert pinned, "no pinned requirements found in requirements.txt"

    mismatches = {
        name: (version, locked.get(normalise(name)))
        for name, version in pinned
        if locked.get(normalise(name)) != version
    }

    assert mismatches == {}, (
        "requirements.txt pins versions that are not in uv.lock "
        "(run `just prepare-pip`): " + ", ".join(sorted(mismatches))
    )
