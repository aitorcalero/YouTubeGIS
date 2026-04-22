"""Custom exceptions for YouTubeGIS."""

from __future__ import annotations


class YouTubeGISError(Exception):
    """Base exception for YouTubeGIS."""

    pass


class YouTubeAPIError(YouTubeGISError):
    """Error accessing YouTube API."""

    pass


class OpenAIError(YouTubeGISError):
    """Error calling OpenAI API for location extraction."""

    pass


class GeocodingError(YouTubeGISError):
    """Error geocoding location names to coordinates."""

    pass


class ArcGISError(YouTubeGISError):
    """Error publishing to or accessing ArcGIS Online."""

    pass


class CredentialsError(YouTubeGISError):
    """Error with missing or invalid credentials."""

    pass


class ConfigurationError(YouTubeGISError):
    """Error with invalid configuration or settings."""

    pass


class ValidationError(YouTubeGISError):
    """Error validating input parameters."""

    pass


class GeoJSONError(YouTubeGISError):
    """Error creating or saving GeoJSON."""

    pass
