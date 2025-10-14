"""
Provider for creating StructuredProcessingLog instances.

This module implements the Factory pattern for processing log creation,
allowing for dependency injection and testability.
"""

from metadata_transformer.processing_log import StructuredProcessingLog


class ProcessingLogProvider:
    """
    Provider for creating StructuredProcessingLog instances.

    This class follows the Factory pattern, encapsulating the creation
    of processing logs. It allows workers to obtain their logs without
    directly instantiating them, improving testability and flexibility.
    """

    def create_log(self) -> StructuredProcessingLog:
        """
        Create a new StructuredProcessingLog instance.

        Returns:
            A fresh StructuredProcessingLog instance for tracking transformations
        """
        return StructuredProcessingLog()
