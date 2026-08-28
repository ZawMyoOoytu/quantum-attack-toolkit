from __future__ import annotations

import math

import pytest

from qattack.analysis.measurement import (
    dominant_probability,
    measurement_probabilities,
    measurement_summary,
    probability_mass,
    shannon_entropy,
)


def test_measurement_probabilities():
    counts = {
        "00": 50,
        "11": 50,
    }

    probabilities = measurement_probabilities(counts)

    assert probabilities["00"] == pytest.approx(0.5)
    assert probabilities["11"] == pytest.approx(0.5)


def test_dominant_probability():
    counts = {
        "00": 70,
        "01": 20,
        "11": 10,
    }

    assert dominant_probability(counts) == pytest.approx(0.7)


def test_uniform_binary_entropy():
    counts = {
        "0": 50,
        "1": 50,
    }

    assert shannon_entropy(counts) == pytest.approx(1.0)


def test_uniform_four_state_entropy():
    counts = {
        "00": 25,
        "01": 25,
        "10": 25,
        "11": 25,
    }

    assert shannon_entropy(counts) == pytest.approx(2.0)


def test_probability_mass():
    counts = {
        "0000": 30,
        "0100": 20,
        "1000": 40,
        "1111": 10,
    }

    mass = probability_mass(
        counts,
        {"0000", "0100", "1000"},
    )

    assert mass == pytest.approx(0.9)


def test_empty_distribution():
    assert measurement_probabilities({}) == {}
    assert dominant_probability({}) == 0.0
    assert shannon_entropy({}) == 0.0


def test_invalid_total():
    with pytest.raises(ValueError):
        measurement_probabilities({
            "00": 0,
            "11": 0,
        })


def test_negative_count():
    with pytest.raises(ValueError):
        measurement_probabilities({
            "00": 10,
            "11": -1,
        })


def test_measurement_summary():
    counts = {
        "0000": 32,
        "0100": 32,
        "1000": 32,
        "1100": 32,
    }

    summary = measurement_summary(counts)

    assert summary["shots"] == 128
    assert summary["unique_states"] == 4
    assert summary["dominant_probability"] == pytest.approx(0.25)
    assert summary["shannon_entropy_bits"] == pytest.approx(2.0)