from __future__ import annotations

from unittest.mock import MagicMock

from api_keys import (
    CREDENTIAL_FIELDS,
    collect_credentials,
    prompt_for_field,
    save_credentials,
)
from YouTubeGIS import Credentials
from config import KEYRING_SERVICE_ID


def test_prompt_for_field_keeps_existing_value_when_not_overwriting() -> None:
    field = CREDENTIAL_FIELDS[0]

    value = prompt_for_field(
        field,
        "existing-value",
        prompt_fn=lambda prompt: "new-value",
        confirm_fn=lambda prompt: False,
    )

    assert value == "existing-value"


def test_collect_credentials_returns_all_values() -> None:
    prompts = iter([
        "openai-key",
        "youtube-key",
        "arcgis-user",
        "arcgis-password",
    ])

    values = collect_credentials(
        Credentials(None, None, None, None),
        prompt_fn=lambda prompt: next(prompts),
        confirm_fn=lambda prompt: True,
    )

    assert values == {
        "OPENAI_API_KEY": "openai-key",
        "YOUTUBE_API_KEY": "youtube-key",
        "USERNAME": "arcgis-user",
        "PWD": "arcgis-password",
    }


def test_save_credentials_persists_all_values(monkeypatch) -> None:
    mock_keyring = MagicMock()
    monkeypatch.setattr("api_keys._import_keyring", lambda: mock_keyring)

    save_credentials(
        KEYRING_SERVICE_ID,
        {
            "OPENAI_API_KEY": "openai-key",
            "YOUTUBE_API_KEY": "youtube-key",
            "USERNAME": "arcgis-user",
            "PWD": "arcgis-password",
        },
    )

    assert mock_keyring.set_password.call_count == 4
    mock_keyring.set_password.assert_any_call(KEYRING_SERVICE_ID, "OPENAI_API_KEY", "openai-key")
    mock_keyring.set_password.assert_any_call(KEYRING_SERVICE_ID, "YOUTUBE_API_KEY", "youtube-key")
    mock_keyring.set_password.assert_any_call(KEYRING_SERVICE_ID, "USERNAME", "arcgis-user")
    mock_keyring.set_password.assert_any_call(KEYRING_SERVICE_ID, "PWD", "arcgis-password")
