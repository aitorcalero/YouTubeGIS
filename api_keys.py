"""Asistente interactivo para configurar credenciales de YouTubeGIS."""

from __future__ import annotations

from dataclasses import dataclass
from getpass import getpass
from typing import Callable

from config import (
    ENV_ARCGIS_PASSWORDS,
    ENV_ARCGIS_USERNAMES,
    ENV_OPENAI_API_KEYS,
    ENV_YOUTUBE_API_KEYS,
    KEYRING_OPENAI_KEY,
    KEYRING_PASSWORD_KEY,
    KEYRING_SERVICE_ID,
    KEYRING_USERNAME_KEY,
    KEYRING_YOUTUBE_KEY,
)
from exceptions import ConfigurationError
from YouTubeGIS import Credentials, _import_keyring, load_credentials, load_credentials_from_environment

PromptFunction = Callable[[str], str]


@dataclass(frozen=True)
class CredentialField:
    """Define cómo pedir y almacenar una credencial."""

    label: str
    keyring_key: str
    env_names: tuple[str, ...]
    secret: bool = True


CREDENTIAL_FIELDS: tuple[CredentialField, ...] = (
    CredentialField("Clave API de OpenAI", KEYRING_OPENAI_KEY, ENV_OPENAI_API_KEYS),
    CredentialField("Clave API de YouTube", KEYRING_YOUTUBE_KEY, ENV_YOUTUBE_API_KEYS),
    CredentialField("Usuario de ArcGIS Online", KEYRING_USERNAME_KEY, ENV_ARCGIS_USERNAMES, secret=False),
    CredentialField("Contraseña de ArcGIS Online", KEYRING_PASSWORD_KEY, ENV_ARCGIS_PASSWORDS),
)


def _read_value(prompt: str, *, secret: bool) -> str:
    """Read a credential value from stdin."""

    value = getpass(prompt) if secret else input(prompt)
    return value.strip()


def _confirm(prompt: str) -> bool:
    """Ask for a yes/no confirmation."""

    answer = input(prompt).strip().lower()
    return answer in {"s", "si", "sí", "y", "yes"}


def _resolve_existing_value(credentials: Credentials, field: CredentialField) -> str | None:
    """Return the current stored value for the requested field."""

    mapping = {
        KEYRING_OPENAI_KEY: credentials.openai_api_key,
        KEYRING_YOUTUBE_KEY: credentials.youtube_api_key,
        KEYRING_USERNAME_KEY: credentials.username,
        KEYRING_PASSWORD_KEY: credentials.password,
    }
    return mapping[field.keyring_key]


def prompt_for_field(
    field: CredentialField,
    current_value: str | None,
    *,
    prompt_fn: PromptFunction | None = None,
    confirm_fn: Callable[[str], bool] | None = None,
) -> str | None:
    """Prompt for one field, optionally preserving an existing value."""

    prompt_fn = prompt_fn or (lambda prompt: _read_value(prompt, secret=field.secret))
    confirm_fn = confirm_fn or _confirm

    if current_value and not confirm_fn(f"Ya existe {field.label}. ¿Quieres sobrescribirla? [s/N]: "):
        return current_value

    while True:
        value = prompt_fn(f"{field.label}: ")
        if value:
            return value
        print("Valor vacío. Inténtalo de nuevo.")


def collect_credentials(
    current_credentials: Credentials,
    *,
    prompt_fn: PromptFunction | None = None,
    confirm_fn: Callable[[str], bool] | None = None,
) -> dict[str, str]:
    """Collect all required credentials interactively."""

    collected: dict[str, str] = {}
    for field in CREDENTIAL_FIELDS:
        current_value = _resolve_existing_value(current_credentials, field)
        value = prompt_for_field(
            field,
            current_value,
            prompt_fn=prompt_fn,
            confirm_fn=confirm_fn,
        )
        if value is None:
            raise ConfigurationError(f"No se pudo obtener un valor válido para {field.label}.")
        collected[field.keyring_key] = value
    return collected


def save_credentials(service_id: str, values: dict[str, str]) -> None:
    """Persist credentials into the OS keyring."""

    keyring = _import_keyring()
    for key, value in values.items():
        keyring.set_password(service_id, key, value)


def print_environment_hints() -> None:
    """Explain the optional environment-variable fallback."""

    print("\nTambién puedes ejecutar el proyecto sin keyring usando variables de entorno:")
    print("- OPENAI_API_KEY")
    print("- YOUTUBE_API_KEY")
    print("- ARCGIS_USERNAME")
    print("- ARCGIS_PASSWORD")

    env_credentials = load_credentials_from_environment()
    if any([env_credentials.openai_api_key, env_credentials.youtube_api_key, env_credentials.username, env_credentials.password]):
        print("Se han detectado algunas credenciales en variables de entorno; se usarán como fallback.")


def main(service_id: str = KEYRING_SERVICE_ID) -> None:
    """Run the interactive credential setup flow."""

    try:
        current_credentials = load_credentials(service_id)
        print("Configuración de credenciales para YouTubeGIS")
        print("Los secretos se guardarán en el almacén seguro del sistema mediante keyring.")
        print_environment_hints()
        values = collect_credentials(current_credentials)
        save_credentials(service_id, values)
        print("\nCredenciales guardadas correctamente en keyring.")
    except ConfigurationError as exc:
        print(f"Error de configuración: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
