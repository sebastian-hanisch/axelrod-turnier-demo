"""Gemeinsame Fixtures (DEMO-PLAYBOOK §1b): feste Zufallsquelle, Auszahlungen 5/3/1/0."""

import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def rng():
    return random.Random(12345)
