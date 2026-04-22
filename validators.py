"""Input validation utilities for YouTubeGIS."""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from .exceptions import ValidationError, ConfigurationError
except ImportError:
    from exceptions import ValidationError, ConfigurationError

if TYPE_CHECKING:
    from typing import Any


CREDENTIALS_HELP = (
    "Configura las credenciales con 'python api_keys.py' o define las variables de entorno "
    "OPENAI_API_KEY, YOUTUBE_API_KEY, ARCGIS_USERNAME y ARCGIS_PASSWORD."
)


def validate_channel_id(channel_id: str) -> None:
    """Validate YouTube channel ID format.
    
    Args:
        channel_id: YouTube channel ID to validate
        
    Raises:
        ValidationError: If channel ID is invalid
    """
    if not channel_id or not isinstance(channel_id, str):
        raise ValidationError("Channel ID must be a non-empty string")

    normalized = channel_id.strip()
    if len(normalized) < 2:
        raise ValidationError("Channel ID must be at least 2 characters")

    # YouTube channel IDs typically start with 'UC' and are alphanumeric
    if not normalized.startswith("UC"):
        raise ValidationError("YouTube channel ID should start with 'UC'")


def validate_num_videos(num_videos: int) -> None:
    """Validate number of videos to process.
    
    Args:
        num_videos: Number of videos
        
    Raises:
        ValidationError: If num_videos is invalid
    """
    if not isinstance(num_videos, int):
        raise ValidationError("Number of videos must be an integer")
    
    if num_videos < 1:
        raise ValidationError("Number of videos must be at least 1")
    
    if num_videos > 100:
        raise ValidationError("Number of videos cannot exceed 100 (YouTube API limits)")


def validate_api_keys(openai_key: str | None, youtube_key: str | None) -> None:
    """Validate that API keys are present.
    
    Args:
        openai_key: OpenAI API key
        youtube_key: YouTube API key
        
    Raises:
        ConfigurationError: If any required API key is missing
    """
    if not openai_key:
        raise ConfigurationError(f"OpenAI API key is missing. {CREDENTIALS_HELP}")
    
    if not youtube_key:
        raise ConfigurationError(f"YouTube API key is missing. {CREDENTIALS_HELP}")


def validate_credentials(username: str | None, password: str | None) -> None:
    """Validate ArcGIS credentials.
    
    Args:
        username: ArcGIS Online username
        password: ArcGIS Online password
        
    Raises:
        ConfigurationError: If credentials are missing
    """
    if not username or not password:
        raise ConfigurationError(f"ArcGIS credentials missing. {CREDENTIALS_HELP}")


def validate_location_name(location_name: str | None) -> None:
    """Validate extracted location name.
    
    Args:
        location_name: Location name to validate
        
    Raises:
        ValidationError: If location name is invalid
    """
    if not location_name or not isinstance(location_name, str):
        raise ValidationError("Location name must be a non-empty string")
    
    if len(location_name.strip()) < 2:
        raise ValidationError("Location name must be at least 2 characters")


def validate_video_title(title: str) -> None:
    """Validate video title format.
    
    Args:
        title: Video title to validate
        
    Raises:
        ValidationError: If title is invalid
    """
    if not title or not isinstance(title, str):
        raise ValidationError("Video title must be a non-empty string")
    
    if len(title.strip()) < 1:
        raise ValidationError("Video title cannot be empty")


def validate_features_list(features: list[Any]) -> None:
    """Validate features list for GeoJSON generation.
    
    Args:
        features: List of GeoJSON features
        
    Raises:
        ValidationError: If features list is invalid
    """
    if not isinstance(features, list):
        raise ValidationError("Features must be a list")
    
    if len(features) == 0:
        raise ValidationError("Features list cannot be empty")


def validate_filename(filename: str | None) -> None:
    """Validate output filename.
    
    Args:
        filename: Filename to validate
        
    Raises:
        ValidationError: If filename is invalid
    """
    if filename is not None:
        if not isinstance(filename, str):
            raise ValidationError("Filename must be a string")
        
        if not filename.endswith(".geojson"):
            raise ValidationError("Filename must end with .geojson extension")
        
        if len(filename) < 10:  # At least "a.geojson"
            raise ValidationError("Filename is too short")
