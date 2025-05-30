import os
import sys
import json
import builtins
import pytest
from unittest import mock
from wnsm_sync.sync_bewegungsdaten_to_ha import load_config

# Import the function to test

@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    """Clear relevant environment variables before each test."""
    keys = [
        "WNSM_USERNAME", "WNSM_PASSWORD", "USE_EXTERNAL_MQTT", "HA_URL", "STAT_ID",
        "MQTT_HOST", "MQTT_PORT", "MQTT_TOPIC", "MQTT_USERNAME", "MQTT_PASSWORD",
        "HISTORY_DAYS", "RETRY_COUNT", "RETRY_DELAY", "UPDATE_INTERVAL", "SESSION_FILE", "WNSM_ZP"
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)

def test_load_config_from_env(monkeypatch):
    monkeypatch.setenv("WNSM_USERNAME", "user1")
    monkeypatch.setenv("WNSM_PASSWORD", "pass1")
    monkeypatch.setenv("WNSM_ZP", "123456789")
    monkeypatch.setenv("MQTT_PORT", "1884")
    monkeypatch.setenv("HISTORY_DAYS", "2")
    monkeypatch.setenv("RETRY_COUNT", "5")
    monkeypatch.setenv("RETRY_DELAY", "7")
    monkeypatch.setenv("UPDATE_INTERVAL", "3600")
    monkeypatch.setenv("SESSION_FILE", "/tmp/session.json")

    # Patch sys.exit to raise SystemExit so we can catch it if called
    with mock.patch.object(sys, "exit", side_effect=SystemExit):
        config = load_config()
    assert config["USERNAME"] == "user1"
    assert config["PASSWORD"] == "pass1"
    assert config["HISTORY_DAYS"] == 2
    assert config["RETRY_COUNT"] == 5
    assert config["RETRY_DELAY"] == 7
    assert config["UPDATE_INTERVAL"] == 3600
    assert config["SESSION_FILE"] == "/tmp/session.json"

def test_load_config_from_options_json(monkeypatch, tmp_path):
    # Remove env vars
    monkeypatch.delenv("WNSM_USERNAME", raising=False)
    monkeypatch.delenv("WNSM_PASSWORD", raising=False)
    monkeypatch.delenv("WNSM_ZP", raising=False)

    # Prepare options.json
    options = {
        "WNSM_USERNAME": "user2",
        "WNSM_PASSWORD": "pass2",
        "WNSM_ZP": "987654321",
        "HISTORY_DAYS": 3,
        "RETRY_COUNT": 4,
        "RETRY_DELAY": 6
    }
    options_path = tmp_path / "options.json"
    with open(options_path, "w") as f:
        json.dump(options, f)

    # Patch open to use our options.json
    def fake_open(path, *args, **kwargs):
        if path == "/data/options.json":
            return builtins.open(options_path, *args, **kwargs)
        return builtins.open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", fake_open)
    # Patch sys.exit to raise SystemExit so we can catch it if called
    with mock.patch.object(sys, "exit", side_effect=SystemExit):
        config = load_config()
    assert config["USERNAME"] == "user2"
    assert config["PASSWORD"] == "pass2"
    assert config["ZP"] == "987654321"
    assert config["HISTORY_DAYS"] == 3
    assert config["RETRY_COUNT"] == 4
    assert config["RETRY_DELAY"] == 6

def test_missing_required_config_exits(monkeypatch):
    # Remove env vars and patch open to raise FileNotFoundError
    monkeypatch.delenv("WNSM_USERNAME", raising=False)
    monkeypatch.delenv("WNSM_PASSWORD", raising=False)
    monkeypatch.delenv("WNSM_ZP", raising=False)
    monkeypatch.setattr("builtins.open", mock.Mock(side_effect=FileNotFoundError))
    with mock.patch.object(sys, "exit", side_effect=SystemExit) as exit_mock:
        with pytest.raises(SystemExit):
            load_config()
        exit_mock.assert_called_once()

def test_options_json_missing_keys(monkeypatch, tmp_path):
    # Only provide USERNAME in options.json, others missing
    options = {
        "WNSM_USERNAME": "user3"
    }
    options_path = tmp_path / "options.json"
    with open(options_path, "w") as f:
        json.dump(options, f)

    monkeypatch.delenv("WNSM_USERNAME", raising=False)
    monkeypatch.delenv("WNSM_PASSWORD", raising=False)
    monkeypatch.delenv("WNSM_ZP", raising=False)

    def fake_open(path, *args, **kwargs):
        if path == "/data/options.json":
            return builtins.open(options_path, *args, **kwargs)
        return builtins.open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", fake_open)
    with mock.patch.object(sys, "exit", side_effect=SystemExit) as exit_mock:
        with pytest.raises(SystemExit):
            load_config()
        exit_mock.assert_called_once()