import sys
from nistoar.pdr.preserv import PreservationException


class ArchivingException(PreservationException):
    """
    Base exception for all archiving-related errors within the archiving client.

    This exception is used as the base class for all exceptions raised specifically
    in the context of archiving operations, providing a unified way to handle all
    archive-related errors.
    """

    def __init__(self, msg=None, errors=None, cause=None):
        """
        Initialize the ArchivingException with a message, a list of detailed errors, and an optional cause.

        :param msg str: A message describing the error.
        :param errors list: A list of specific error messages with details.
        :param cause Exception: An underlying cause in the form of an Exception.
        """
        super().__init__(msg=msg, errors=errors, cause=cause)


class SQSException(ArchivingException):
    """
    Specific exception for handling errors related to interactions with AWS SQS.

    This subclass captures exceptions that are specific to SQS operations and provides
    more detail.
    """

    def __init__(self, original_exception, message=None):
        """
        Initialize the SQSException with the original exception thrown by AWS SQS and an optional custom message.

        :param original_exception Exception: The original exception thrown by AWS SQS.
        :param message str: Optional custom message to provide additional context about the error.
        """
        default_message = f"An error occurred with SQS: {str(original_exception)}"
        super().__init__(
            msg=message if message else default_message, cause=original_exception
        )


class ValidationException(ArchivingException):
    """
    An exception indicating a failure in validating data against predefined schemas
    or rules within the archiving process.

    This exception is used to highlight problems with the data being processed that
    do not meet the required standards or expectations, such as format, completeness,
    or logical consistency.
    """

    def __init__(self, message, errors=None, cause=None):
        """
        Initializes a new instance of ValidationException.

        :param message str: A general message describing the validation failure.
        :param errors list: A list of specific error messages providing
                                        detailed information about what failed during
                                        validation.
        :param cause Exception: An underlying cause in the form of an
                                            Exception instance, providing more context
                                            about the source of the failure.
        """
        super().__init__(msg=message, errors=errors, cause=cause)
