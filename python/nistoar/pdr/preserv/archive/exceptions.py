class SQSException(Exception):
    """Custom exception for handling SQS specific errors."""

    def __init__(self, original_exception, message=None):
        self.original_exception = original_exception
        if message is None:
            message = f"An error occurred with SQS: {str(original_exception)}"
        super().__init__(message)
