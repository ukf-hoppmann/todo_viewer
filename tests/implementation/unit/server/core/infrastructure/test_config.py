import json
from pathlib import Path

import pytest
from viewer.core.infrastructure.config import ConfigError, load_settings


def test_defaults_without_file() -> None:
    s = load_settings(Path("/nonexistent/viewer.json"), env={})
    assert (s.host, s.port, s.sse_keepalive_seconds) == ("127.0.0.1", 5411, 15.0)
    assert s.for_plugin("x") == {}


def test_file_values_and_plugin_section(tmp_path: Path) -> None:
    f = tmp_path / "viewer.json"
    f.write_text(json.dumps({"port": 6000, "plugins": {"alarms": {"x": 1}}}), encoding="utf-8")
    s = load_settings(f, env={})
    assert s.port == 6000
    assert s.for_plugin("alarms") == {"x": 1}


def test_environment_beats_file(tmp_path: Path) -> None:
    f = tmp_path / "viewer.json"
    f.write_text(json.dumps({"port": 6000}), encoding="utf-8")
    assert load_settings(f, env={"VIEWER_PORT": "7000"}).port == 7000
    other = tmp_path / "other.json"
    other.write_text(json.dumps({"port": 1}), encoding="utf-8")
    assert load_settings(f, env={"VIEWER_CONFIG": str(other)}).port == 1


@pytest.mark.parametrize("content", ["{kaputt", "[]", json.dumps({"port": "abc"}), json.dumps({"plugins": []})])
def test_invalid_config_raises_config_error(tmp_path: Path, content: str) -> None:
    f = tmp_path / "viewer.json"
    f.write_text(content, encoding="utf-8")
    with pytest.raises(ConfigError) as err:
        load_settings(f, env={})
    assert err.value.code == "config_invalid"
