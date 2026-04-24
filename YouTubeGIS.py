"""Core workflow for extracting geographic locations from YouTube titles."""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import string
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

from config import (
    ARCGIS_BASE_URL,
    ARCGIS_FEATURE_SERVICE_TAGS,
    ARCGIS_PORTAL,
    CHANNEL_SELECTION_TITLE,
    DEFAULT_PICK_INDICATOR,
    ENV_ARCGIS_PASSWORDS,
    ENV_ARCGIS_USERNAMES,
    ENV_OPENAI_API_KEYS,
    ENV_YOUTUBE_API_KEYS,
    GEOJSON_ENCODING,
    GEOJSON_INDENT,
    KEYRING_OPENAI_KEY,
    KEYRING_PASSWORD_KEY,
    KEYRING_SERVICE_ID,
    KEYRING_USERNAME_KEY,
    KEYRING_YOUTUBE_KEY,
    LOG_FORMAT,
    LOG_LEVEL,
    MAX_GEOCODING_RESULTS,
    OPENAI_LOCATION_PROMPT_TEMPLATE,
    OPENAI_MAX_TOKENS,
    OPENAI_MODEL,
    OPENAI_SYSTEM_PROMPT,
    OPENAI_TEMPERATURE,
    OUTPUT_DIR,
    RANDOM_STRING_LENGTH,
    TIMESTAMP_FORMAT,
    VIDEO_COUNT_TITLE,
    YOUTUBE_API_VERSION,
    YOUTUBE_SEARCH_ORDER,
    YOUTUBE_SEARCH_TYPE,
)
from exceptions import (
    ArcGISError,
    ConfigurationError,
    GeoJSONError,
    GeocodingError,
    OpenAIError as OpenAIServiceError,
    YouTubeAPIError,
    YouTubeGISError,
    ValidationError,
)
from validators import (
    validate_api_keys,
    validate_channel_id,
    validate_credentials,
    validate_features_list,
    validate_filename,
    validate_location_name,
    validate_num_videos,
    validate_video_title,
)


logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format=LOG_FORMAT,
)
LOGGER = logging.getLogger(__name__)

DEFAULT_CHANNELS: tuple[str, ...] = (
    "UCdwdFOhBP9CoAOlHDTmTxaw | Un Mundo Inmmenso",
    "UCknQM__AyaqSdxunkqpavDg | Misias pero Viajeras",
    "UCRTq5KxoyKuquatzn2iF0Pg | Military Lab",
    "UCmmPgObSUPw1HL2lq6H4ffA | GeographyNow",
)
DEFAULT_VIDEO_COUNTS: tuple[str, ...] = ("1", "5", "10", "15", "20", "50")
NO_LOCATION_RESPONSES: frozenset[str] = frozenset(
    {
        "",
        "none",
        "ninguna",
        "n/a",
        "sin ubicacion clara",
        "sin ubicación clara",
        "no clear location",
        "no location",
        "unknown",
    }
)


@dataclass(frozen=True)
class Credentials:
    """Authentication material required by the workflow."""

    openai_api_key: str | None
    youtube_api_key: str | None
    username: str | None
    password: str | None


def _clean_credential(value: str | None) -> str | None:
    """Normalize blank credential values to None."""

    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _get_first_environment_value(variable_names: Sequence[str]) -> str | None:
    """Return the first non-empty environment variable value from a list of names."""

    for variable_name in variable_names:
        value = _clean_credential(os.getenv(variable_name))
        if value:
            return value
    return None


def load_credentials_from_environment() -> Credentials:
    """Load supported credentials from environment variables."""

    return Credentials(
        openai_api_key=_get_first_environment_value(ENV_OPENAI_API_KEYS),
        youtube_api_key=_get_first_environment_value(ENV_YOUTUBE_API_KEYS),
        username=_get_first_environment_value(ENV_ARCGIS_USERNAMES),
        password=_get_first_environment_value(ENV_ARCGIS_PASSWORDS),
    )


def merge_credentials(primary: Credentials, fallback: Credentials) -> Credentials:
    """Merge two credential sets, preferring the primary values."""

    return Credentials(
        openai_api_key=primary.openai_api_key or fallback.openai_api_key,
        youtube_api_key=primary.youtube_api_key or fallback.youtube_api_key,
        username=primary.username or fallback.username,
        password=primary.password or fallback.password,
    )


def _describe_credentials(credentials: Credentials) -> str:
    """Return a compact description of which credentials are available."""

    status = {
        "OpenAI": bool(credentials.openai_api_key),
        "YouTube": bool(credentials.youtube_api_key),
        "ArcGIS username": bool(credentials.username),
        "ArcGIS password": bool(credentials.password),
    }
    available = [name for name, present in status.items() if present]
    return ", ".join(available) if available else "none"


def _missing_credentials_message() -> str:
    """Build a reusable guidance message for missing credentials."""

    return (
        "Configura las credenciales con 'python api_keys.py' o define las variables de entorno "
        "OPENAI_API_KEY, YOUTUBE_API_KEY, ARCGIS_USERNAME y ARCGIS_PASSWORD."
    )


def _load_keyring_credentials(service_id: str) -> Credentials:
    """Load stored credentials from the OS keyring."""

    keyring = _import_keyring()
    return Credentials(
        openai_api_key=_clean_credential(keyring.get_password(service_id, KEYRING_OPENAI_KEY)),
        youtube_api_key=_clean_credential(keyring.get_password(service_id, KEYRING_YOUTUBE_KEY)),
        username=_clean_credential(keyring.get_password(service_id, KEYRING_USERNAME_KEY)),
        password=_clean_credential(keyring.get_password(service_id, KEYRING_PASSWORD_KEY)),
    )


def _credentials_available(credentials: Credentials) -> bool:
    """Return True when at least one credential value is present."""

    return any(
        [
            credentials.openai_api_key,
            credentials.youtube_api_key,
            credentials.username,
            credentials.password,
        ]
    )


def _import_keyring() -> Any:
    try:
        import keyring
    except ImportError as exc:
        raise ConfigurationError(
            "Missing dependency 'keyring'. Install the project requirements first."
        ) from exc
    return keyring


def _import_openai_client_class() -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ConfigurationError(
            "Missing dependency 'openai'. Install the project requirements first."
        ) from exc
    return OpenAI


def _import_youtube_build() -> Any:
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise ConfigurationError(
            "Missing dependency 'google-api-python-client'. Install the project requirements first."
        ) from exc
    return build


def _import_arcgis_geocode() -> Any:
    try:
        from arcgis.geocoding import geocode
    except ImportError as exc:
        raise ConfigurationError(
            "Missing dependency 'arcgis'. Install the project requirements first."
        ) from exc
    return geocode


def _import_arcgis_gis_class() -> Any:
    try:
        from arcgis.gis import GIS
    except ImportError as exc:
        raise ConfigurationError(
            "Missing dependency 'arcgis'. Install the project requirements first."
        ) from exc
    return GIS


def _import_arcgis_content_types() -> tuple[Any, Any]:
    try:
        from arcgis.gis import ItemProperties, ItemTypeEnum
    except ImportError as exc:
        raise ConfigurationError(
            "Missing dependency 'arcgis'. Install the project requirements first."
        ) from exc
    return ItemProperties, ItemTypeEnum


def _import_pick() -> Any:
    try:
        from pick import pick
    except ImportError as exc:
        raise ConfigurationError(
            "Missing dependency 'pick'. Install the project requirements first."
        ) from exc
    return pick


def load_credentials(service_id: str = KEYRING_SERVICE_ID) -> Credentials:
    """Load credentials from keyring first and complete missing values from the environment."""

    keyring_credentials = Credentials(None, None, None, None)
    try:
        keyring_credentials = _load_keyring_credentials(service_id)
    except Exception as exc:
        LOGGER.info(
            "No se pudieron cargar credenciales desde keyring (%s); se intentarán variables de entorno.",
            exc.__class__.__name__,
        )

    env_credentials = load_credentials_from_environment()
    credentials = merge_credentials(keyring_credentials, env_credentials)

    if not _credentials_available(credentials):
        LOGGER.warning("No se encontraron credenciales configuradas. %s", _missing_credentials_message())
    elif _credentials_available(env_credentials):
        LOGGER.info(
            "Credenciales resueltas con soporte de variables de entorno: %s",
            _describe_credentials(credentials),
        )

    return credentials


def get_api_keys(service_id: str = KEYRING_SERVICE_ID) -> tuple[str | None, str | None, str | None, str | None]:
    """Backward-compatible wrapper returning the configured secrets as a tuple."""

    credentials = load_credentials(service_id)
    return (
        credentials.openai_api_key,
        credentials.youtube_api_key,
        credentials.username,
        credentials.password,
    )


def normalize_location_name(raw_location: str | None) -> str | None:
    """Normalize a model response into a usable location name."""

    if raw_location is None:
        return None

    normalized = raw_location.strip().strip("\"'").strip()
    if normalized.casefold() in NO_LOCATION_RESPONSES:
        return None
    return normalized or None


def extract_location_with_openai(title: str, api_key: str | None) -> str | None:
    """Extract the most likely geographic location from a title."""

    validate_video_title(title)
    if not api_key:
        raise ConfigurationError(
            f"OpenAI API key is missing. {_missing_credentials_message()}"
        )

    LOGGER.info("Extracting location from title with OpenAI: %s", title)
    openai_client_class = _import_openai_client_class()

    try:
        client = openai_client_class(api_key=api_key)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": OPENAI_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": OPENAI_LOCATION_PROMPT_TEMPLATE.format(title=title),
                },
            ],
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS,
        )
    except Exception as exc:
        raise OpenAIServiceError(f"Error while calling OpenAI API: {exc}") from exc

    if not getattr(response, "choices", None):
        return None

    content = response.choices[0].message.content
    return normalize_location_name(content)


def generate_random_string(length: int = RANDOM_STRING_LENGTH) -> str:
    """Generate a timestamped random string for output filenames."""

    if length < 1:
        raise ValidationError("Random string length must be greater than zero")

    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
    random_suffix = "".join(random.choice(string.ascii_lowercase) for _ in range(length))
    return f"{timestamp}_{random_suffix}"


def resolve_portal_url(gis: Any | None = None, fallback_portal_url: str = ARCGIS_PORTAL) -> str:
    """Resolve the ArcGIS portal URL from the active GIS connection."""

    portal_url = (
        getattr(gis, "url", None)
        or getattr(getattr(gis, "_portal", None), "url", None)
        or fallback_portal_url
    )
    normalized = portal_url.rstrip("/")
    if normalized.endswith("/sharing/rest"):
        normalized = normalized[: -len("/sharing/rest")]
    return normalized


def build_feature_service_url(
    feature_service_id: str,
    portal_url: str = ARCGIS_PORTAL,
) -> str:
    """Build a browser URL for a published ArcGIS item."""

    if not feature_service_id or not isinstance(feature_service_id, str):
        raise ValidationError("Feature service ID must be a non-empty string")

    base_url = resolve_portal_url(fallback_portal_url=portal_url)
    if base_url == ARCGIS_PORTAL and ARCGIS_BASE_URL.startswith(base_url):
        return f"{ARCGIS_BASE_URL}{feature_service_id}"
    return f"{base_url}/home/item.html?id={feature_service_id}"


def open_feature_service_in_browser(
    feature_service_id: str,
    portal_url: str = ARCGIS_PORTAL,
) -> str:
    """Open the published ArcGIS item in the default browser."""

    full_url = build_feature_service_url(feature_service_id, portal_url)
    webbrowser.open(full_url, new=2)
    return full_url


def build_feature_service_url_only(
    feature_service_id: str,
    portal_url: str = ARCGIS_PORTAL,
) -> str:
    """Build the published ArcGIS item URL without opening a browser."""

    return build_feature_service_url(feature_service_id, portal_url)


def save_to_geojson(features: list[dict[str, Any]], filename: str | None = None) -> str:
    """Save features to a GeoJSON file inside the output directory."""

    validate_features_list(features)
    if filename is None:
        filename = f"{generate_random_string()}.geojson"
    validate_filename(filename)

    output_dir = Path(__file__).resolve().parent / OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / filename

    geojson = {"type": "FeatureCollection", "features": features}

    try:
        filepath.write_text(
            json.dumps(geojson, ensure_ascii=False, indent=GEOJSON_INDENT),
            encoding=GEOJSON_ENCODING,
        )
    except OSError as exc:
        raise GeoJSONError(f"Error writing GeoJSON file: {exc}") from exc

    LOGGER.info("GeoJSON file generated successfully at %s", filepath)
    return str(filepath)


def create_features_from_locations(
    titles: Sequence[str],
    location_names: Sequence[str | None],
    locations: Sequence[dict[str, float] | None],
) -> list[dict[str, Any]]:
    """Create GeoJSON features from aligned titles, names and coordinates."""

    if not (len(titles) == len(location_names) == len(locations)):
        raise ValidationError(
            "Titles, location names and locations must contain the same number of items"
        )

    features: list[dict[str, Any]] = []
    for title, location_name, location in zip(titles, location_names, locations):
        validate_video_title(title)
        if not location_name or not location:
            continue

        validate_location_name(location_name)
        if "x" not in location or "y" not in location:
            LOGGER.warning("Skipping invalid geocoding payload for location %s", location_name)
            continue

        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [location["x"], location["y"]]},
            "properties": {"Title": title, "Location": location_name},
        }
        features.append(feature)
    return features


def geocode_location(location_name: str) -> dict[str, float] | None:
    """Geocode a location name into ArcGIS coordinates."""

    validate_location_name(location_name)
    LOGGER.info("Geocoding location: %s", location_name)

    geocode = _import_arcgis_geocode()
    try:
        geocoding_result = geocode(location_name, max_locations=MAX_GEOCODING_RESULTS)
    except Exception as exc:
        raise GeocodingError(
            f"Error geocoding location '{location_name}': {exc}"
        ) from exc

    if geocoding_result:
        return geocoding_result[0].get("location")

    LOGGER.warning("No geocoding result for location: %s", location_name)
    return None


def geocode_locations(location_names: Sequence[str]) -> list[dict[str, float] | None]:
    """Geocode a batch of location names while preserving input order."""

    results: list[dict[str, float] | None] = []
    for location_name in location_names:
        try:
            results.append(geocode_location(location_name))
        except (ValidationError, GeocodingError) as exc:
            LOGGER.warning("%s", exc)
            results.append(None)
    return results


def extract_location_pairs_from_titles(
    titles: Sequence[str],
    openai_api_key: str | None,
) -> tuple[list[str], list[str]]:
    """Return aligned titles and location names for successful extractions."""

    if not openai_api_key:
        raise ConfigurationError(
            f"OpenAI API key is missing. {_missing_credentials_message()}"
        )

    matched_titles: list[str] = []
    location_names: list[str] = []
    for title in titles:
        try:
            location_name = extract_location_with_openai(title, openai_api_key)
        except (ValidationError, OpenAIServiceError) as exc:
            LOGGER.warning("%s", exc)
            continue

        if location_name:
            matched_titles.append(title)
            location_names.append(location_name)

    return matched_titles, location_names


def extract_locations_from_titles(
    titles: Sequence[str],
    openai_api_key: str | None,
) -> list[str]:
    """Backward-compatible wrapper returning only the extracted location names."""

    _, location_names = extract_location_pairs_from_titles(titles, openai_api_key)
    return location_names


def get_youtube_videos(
    youtube_api_key: str | None,
    channel_id: str,
    max_results: int,
) -> list[str]:
    """Fetch video titles from a YouTube channel."""

    validate_channel_id(channel_id)
    validate_num_videos(max_results)
    if not youtube_api_key:
        raise ConfigurationError(
            f"YouTube API key is missing. {_missing_credentials_message()}"
        )

    build = _import_youtube_build()
    try:
        youtube = build("youtube", YOUTUBE_API_VERSION, developerKey=youtube_api_key)
        request = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            maxResults=max_results,
            order=YOUTUBE_SEARCH_ORDER,
            type=YOUTUBE_SEARCH_TYPE,
        )
        response = request.execute()
    except Exception as exc:
        raise YouTubeAPIError(f"Error fetching YouTube videos: {exc}") from exc

    return [
        item["snippet"]["title"]
        for item in response.get("items", [])
        if item.get("snippet", {}).get("title")
    ]


def create_gis_connection(username: str | None, password: str | None) -> Any:
    """Create an authenticated GIS session."""

    validate_credentials(username, password)
    gis_class = _import_arcgis_gis_class()

    try:
        return gis_class(ARCGIS_PORTAL, username, password)
    except Exception as exc:
        raise ArcGISError(f"Error connecting to ArcGIS Online: {exc}") from exc


def get_root_folder(gis: Any) -> Any:
    """Return the root folder for the authenticated GIS user."""

    owner = getattr(getattr(gis, "users", None), "me", None)
    try:
        folder = gis.content.folders.get(owner=owner)
    except Exception as exc:
        raise ArcGISError(f"Error resolving the ArcGIS root folder: {exc}") from exc

    if folder is None:
        raise ArcGISError("Could not resolve the ArcGIS root folder for the current user.")
    return folder


def publish_geojson_as_feature_service(gis: Any, filepath: str) -> Any:
    """Publish a GeoJSON file to ArcGIS Online and return the published item."""

    path = Path(filepath)
    if not path.exists():
        raise GeoJSONError(f"GeoJSON file does not exist: {filepath}")
    validate_filename(path.name)

    LOGGER.info("Publishing GeoJSON file to ArcGIS: %s", path.name)
    item_properties_class, item_type_enum = _import_arcgis_content_types()
    folder = get_root_folder(gis)
    item_properties = item_properties_class(
        title=path.stem,
        item_type=item_type_enum.GEOJSON,
        tags=list(ARCGIS_FEATURE_SERVICE_TAGS),
        file_name=path.name,
    )

    try:
        add_job = folder.add(item_properties=item_properties, file=str(path))
        item = add_job.result()
        published_item = item.publish()
    except Exception as exc:
        raise ArcGISError(f"Error publishing GeoJSON to ArcGIS: {exc}") from exc

    LOGGER.info("GeoJSON published as Feature Service with ID: %s", published_item.id)
    return published_item


def process_and_publish_videos(
    youtube_api_key: str | None,
    openai_api_key: str | None,
    channel_id: str,
    num_videos: int,
    *,
    arcgis_credentials: Credentials | None = None,
    open_browser: bool = True,
    dry_run: bool = False,
) -> Any | None:
    """Run the end-to-end workflow from YouTube extraction to ArcGIS publishing."""

    validate_channel_id(channel_id)
    validate_num_videos(num_videos)
    validate_api_keys(openai_api_key, youtube_api_key)

    credentials = arcgis_credentials or load_credentials(KEYRING_SERVICE_ID)
    validate_credentials(credentials.username, credentials.password)
    gis = create_gis_connection(credentials.username, credentials.password)

    titles = get_youtube_videos(youtube_api_key, channel_id, num_videos)
    matched_titles, location_names = extract_location_pairs_from_titles(
        titles, openai_api_key
    )
    if not location_names:
        LOGGER.warning("No locations were extracted from the selected videos.")
        return None

    locations = geocode_locations(location_names)
    features = create_features_from_locations(matched_titles, location_names, locations)
    if not features:
        LOGGER.warning("No valid features were generated. Skipping publication.")
        return None

    filepath = save_to_geojson(features)
    if dry_run:
        LOGGER.info("Dry run enabled; skipping ArcGIS publication. GeoJSON saved at %s", filepath)
        return filepath

    published_item = publish_geojson_as_feature_service(gis, filepath)
    if open_browser:
        open_feature_service_in_browser(
            published_item.id,
            portal_url=resolve_portal_url(gis),
        )
    return published_item


def yt_channel_selection() -> str:
    """Interactively select a YouTube channel."""

    pick = _import_pick()
    option, _ = pick(DEFAULT_CHANNELS, CHANNEL_SELECTION_TITLE, DEFAULT_PICK_INDICATOR)
    return option.split("|", maxsplit=1)[0].strip()


def num_videos() -> str:
    """Interactively select how many videos to process."""

    pick = _import_pick()
    option, _ = pick(DEFAULT_VIDEO_COUNTS, VIDEO_COUNT_TITLE, DEFAULT_PICK_INDICATOR)
    return option


def _resolve_channel_id(channel_id: str | None) -> str:
    """Resolve a channel id from CLI input or interactive selection."""

    return channel_id or yt_channel_selection()


def _resolve_num_videos(num_videos_value: int | None) -> int:
    """Resolve a video count from CLI input or interactive selection."""

    return num_videos_value if num_videos_value is not None else int(num_videos())


def _resolve_credentials_from_args(args: argparse.Namespace) -> Credentials:
    """Resolve ArcGIS credentials from CLI arguments or the configured stores."""

    cli_credentials = Credentials(
        openai_api_key=args.openai_api_key,
        youtube_api_key=args.youtube_api_key,
        username=args.arcgis_username,
        password=args.arcgis_password,
    )
    if any(
        [
            cli_credentials.openai_api_key,
            cli_credentials.youtube_api_key,
            cli_credentials.username,
            cli_credentials.password,
        ]
    ):
        return merge_credentials(cli_credentials, load_credentials(KEYRING_SERVICE_ID))
    return load_credentials(KEYRING_SERVICE_ID)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for non-interactive execution."""

    parser = argparse.ArgumentParser(description="Run the YouTubeGIS workflow.")
    parser.add_argument("--channel-id", help="YouTube channel ID to process")
    parser.add_argument(
        "--num-videos",
        type=int,
        help="Number of recent videos to process",
    )
    parser.add_argument("--openai-api-key", help="OpenAI API key")
    parser.add_argument("--youtube-api-key", help="YouTube API key")
    parser.add_argument("--arcgis-username", help="ArcGIS Online username")
    parser.add_argument("--arcgis-password", help="ArcGIS Online password")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open the published Feature Service in a browser",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate GeoJSON and stop before publishing to ArcGIS",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """Entry point for interactive or parameterized execution."""

    try:
        args = parse_args(argv)
        credentials = _resolve_credentials_from_args(args)
        process_and_publish_videos(
            credentials.youtube_api_key,
            credentials.openai_api_key,
            _resolve_channel_id(args.channel_id),
            _resolve_num_videos(args.num_videos),
            arcgis_credentials=Credentials(
                openai_api_key=credentials.openai_api_key,
                youtube_api_key=credentials.youtube_api_key,
                username=credentials.username,
                password=credentials.password,
            ),
            open_browser=not args.no_browser,
            dry_run=args.dry_run,
        )
    except YouTubeGISError as exc:
        LOGGER.error("%s", exc)


if __name__ == "__main__":
    main()
