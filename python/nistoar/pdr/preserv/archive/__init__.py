from .client import SQSArchiveClient, MockArchiveClient


def create_client(config):
    """Create and return an archive client based on the specified configuration."""
    client_type = config.get("client_type")
    if client_type == "sqs":
        return SQSArchiveClient(config)
    elif client_type == "mock":
        return MockArchiveClient()
    else:
        raise UnsupportedClientTypeException(client_type)


class ConfigurationException(Exception):
    """
    Exception raised for errors that are related to the application configuration.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class UnsupportedClientTypeException(ConfigurationException):
    """Exception raised when an unsupported client type is specified."""

    def __init__(self, client_type, message=None):
        if message is None:
            message = (
                f"Unsupported client type '{client_type}'. Expected 'sqs' or 'mock'."
            )
        super().__init__(message)


class SQSException(Exception):
    """Custom exception for handling SQS specific errors."""

    def __init__(self, original_exception, message=None):
        self.original_exception = original_exception
        if message is None:
            message = f"An error occurred with SQS: {str(original_exception)}"
        super().__init__(message)
