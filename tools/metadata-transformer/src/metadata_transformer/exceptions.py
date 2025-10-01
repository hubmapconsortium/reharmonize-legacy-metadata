"""
Custom exceptions for the metadata transformer package.
"""


class MetadataTransformerError(Exception):
    """Base exception for all metadata transformer errors."""

    pass


class FieldMappingError(MetadataTransformerError):
    """Raised when there are issues with field mapping operations."""

    pass


class ValueMappingError(MetadataTransformerError):
    """Raised when there are issues with value mapping operations."""

    pass


class SchemaValidationError(MetadataTransformerError):
    """Raised when schema validation fails."""

    pass


class FileProcessingError(MetadataTransformerError):
    """Raised when file processing operations fail."""

    pass
