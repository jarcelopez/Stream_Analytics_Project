from __future__ import annotations

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from stream_analytics.common.config import load_typed_config
from stream_analytics.generator.config_models import GeneratorConfig


def _write_temp_yaml(tmp_path: Path, content: str) -> Path:
    cfg_path = tmp_path / "generator.yaml"
    cfg_path.write_text(content, encoding="utf-8")
    return cfg_path


def test_generator_config_valid_from_yaml(tmp_path, monkeypatch):
    content = """
zone_count: 4
restaurant_count: 12
courier_count: 20
demand_level: high
events_per_second: 75
"""
    cfg_path = _write_temp_yaml(tmp_path, content)

    # Point project root helper at our tmp directory
    monkeypatch.setenv("PYTEST_PROJECT_ROOT_OVERRIDE", str(tmp_path))

    config = load_typed_config(
        relative_yaml_path="generator.yaml",
        model_type=GeneratorConfig,
        env_prefix="GENERATOR_",
    )
    assert config.zone_count == 4
    assert config.restaurant_count == 12
    assert config.courier_count == 20
    assert config.demand_level == "high"
    assert config.events_per_second == 75


def test_generator_config_invalid_negative_counts(tmp_path, monkeypatch):
    content = """
zone_count: -1
restaurant_count: 10
courier_count: 5
"""
    cfg_path = _write_temp_yaml(tmp_path, content)
    monkeypatch.setenv("PYTEST_PROJECT_ROOT_OVERRIDE", str(tmp_path))

    with pytest.raises(ValidationError):
        load_typed_config(
            relative_yaml_path="generator.yaml",
            model_type=GeneratorConfig,
            env_prefix="GENERATOR_",
        )


def test_env_overrides_applied(monkeypatch, tmp_path):
    content = """
zone_count: 3
restaurant_count: 10
courier_count: 15
"""
    cfg_path = _write_temp_yaml(tmp_path, content)
    monkeypatch.setenv("PYTEST_PROJECT_ROOT_OVERRIDE", str(tmp_path))
    monkeypatch.setenv("GENERATOR_ZONE_COUNT", "8")
    monkeypatch.setenv("GENERATOR_EVENTS_PER_SECOND", "120.5")

    config = load_typed_config(
        relative_yaml_path="generator.yaml",
        model_type=GeneratorConfig,
        env_prefix="GENERATOR_",
    )
    assert config.zone_count == 8
    assert config.events_per_second == pytest.approx(120.5)


def test_generator_config_invalid_demand_level(tmp_path, monkeypatch):
    content = """
zone_count: 3
restaurant_count: 10
courier_count: 15
demand_level: ultra
"""
    cfg_path = _write_temp_yaml(tmp_path, content)
    monkeypatch.setenv("PYTEST_PROJECT_ROOT_OVERRIDE", str(tmp_path))

    with pytest.raises(ValidationError):
        load_typed_config(
            relative_yaml_path="generator.yaml",
            model_type=GeneratorConfig,
            env_prefix="GENERATOR_",
        )


def test_generator_config_invalid_upper_bounds(tmp_path, monkeypatch):
    content = """
zone_count: 0
restaurant_count: 6000
courier_count: 6000
events_per_second: 20000
"""
    cfg_path = _write_temp_yaml(tmp_path, content)
    monkeypatch.setenv("PYTEST_PROJECT_ROOT_OVERRIDE", str(tmp_path))

    with pytest.raises(ValidationError):
        load_typed_config(
            relative_yaml_path="generator.yaml",
            model_type=GeneratorConfig,
            env_prefix="GENERATOR_",
        )


def test_generator_config_invalid_debug_and_sample_fields(tmp_path, monkeypatch):
    content = """
zone_count: 3
restaurant_count: 10
courier_count: 15
debug_mode_max_events_per_second: -5
debug_mode_max_entity_count: 0
sample_batch_size_per_feed: 0
"""
    cfg_path = _write_temp_yaml(tmp_path, content)
    monkeypatch.setenv("PYTEST_PROJECT_ROOT_OVERRIDE", str(tmp_path))

    with pytest.raises(ValidationError):
        load_typed_config(
            relative_yaml_path="generator.yaml",
            model_type=GeneratorConfig,
            env_prefix="GENERATOR_",
        )

