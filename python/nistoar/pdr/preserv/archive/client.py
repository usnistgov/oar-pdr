import hashlib
import json
import logging
import os
import sys
from datetime import datetime

# Add the root directory of the project to the PYTHONPATH
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
)

from abc import ABCMeta, abstractmethod


from jsonschema import ValidationError
from nistoar.pdr.exceptions import ConfigurationException

from nistoar.pdr.preserv.archive.exceptions import SQSException, ValidationException

logger = logging.getLogger("archive.client")


try:
    import boto3
except ImportError:
    logger.warning("No module named botocore or boto3. You may need to install boto3")
    sys.exit(1)

boto3.compat.filter_python_deprecation_warnings()

from botocore.exceptions import (
    ClientError,
    NoCredentialsError,
    PartialCredentialsError,
    ParamValidationError,
)

DEFAULT_MAX_MESSAGES = 10  # Max number of messages to be polled
DEFAULT_WAIT_TIME = 20  # 20s for long polling


class ArchiveClient(object):
    """
    An abstract base class that defines the interface for an archive client.

    This class provides an API for archive operations like sending archive requests,
    receiving completion messages, and deleting messages from the queue. Implementations
    of this class must provide concrete methods for each of these operations, adapted
    to the specific message queue system they interact with (e.g., AWS SQS).

    The class encapsulates the queue operations needed for the archive client,
    ensuring that derived classes adhere to a consistent interface for these operations.
    This design makes it easy to swap between different queue systems and simplifies
    unit testing by allowing the use of a mock implementation.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def request_archive(self, aipid, filenames, priority=None):
        """
        Sends an archive request to the queue system.

        :param message str: The message to be sent. Must be in JSON format and conforming to the message schema).

        :return dict: A response from the queue system that typically includes details like
                      message ID and status. Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def receive_completion_message(self):
        """
        Receives a message from the queue system indicating the completion of an archiving task.

        :return dict: A message indicating completion details, which typically includes success or
                      failure status, and any relevant data or error messages. Must be implemented
                      by subclasses.
        """
        pass

    @abstractmethod
    def delete_message(self, receipt_handle):
        """
        Deletes a message from the queue using the provided receipt handle. This method is
        typically used to remove a message once it has been successfully processed, to prevent
        it from being processed again.

        :param receipt_handle str: The receipt handle of the message to be deleted.
                                   Must be implemented by subclasses.
        """
        pass


class MockArchiveClient(ArchiveClient):
    """
    A mock implementation of the ArchiveClient for testing purposes.
    This client simulates interactions with a message queue system without performing
    any real network operations. It stores messages in-memory and allows for basic
    operations like sending and receiving messages, mimicking the behavior expected
    from a real archive client in a test environment.

    :attr messages list: A list used to simulate the sending queue where messages are stored after being sent.
    :attr completed_messages list: A list to simulate received messages from the queue,
                                     mimicking the completion queue.
    """

    def __init__(self):
        """
        Initializes the mock client with empty lists for messages and completed messages.
        """
        self.messages = []
        self.completed_messages = []

    def request_archive(self, aipid, filenames, priority=None):
        """
        Simulates sending an archive request by adding the message to the 'messages' list.
        Generates a unique hash ID based on the message content.

        :param message str: The message to be sent. Must be in JSON format and conforming to the message schema).

        :return dict: A mock response dictionary indicating successful message sending, which includes a unique message ID
                      based on the hash of the message content and HTTP status code.
        """
        message = json.dumps(
            {"aipid": aipid, "filenames": filenames, "priority": priority or "medium"}
        )
        # Generate a hash ID based on the message content
        message_id = hashlib.sha256(message.encode("utf-8")).hexdigest()
        self.messages.append(message)
        return {"MessageId": message_id, "ResponseMetadata": {"HTTPStatusCode": 200}}

    def receive_completion_message(self):
        """
        Simulates the reception of a completion message from the queue.

        :return dict: A mock message retrieved from the 'messages' list, if any messages are present.
                      Returns an empty dictionary if no messages are available.
        """
        if self.messages:
            return {
                "Messages": [
                    {"Body": self.messages.pop(0), "ReceiptHandle": "mockhandle"}
                ]
            }
        return {}

    def delete_message(self, receipt_handle):
        """
        Simulates deleting a message from the queue. In this mock implementation,
        this method does nothing. It only serves to demonstrate an API call.
        """
        pass


class SQSArchiveClient(ArchiveClient):
    """
    SQSArchiveClient provides a concrete implementation of the ArchiveClient,
    specifically for interacting with AWS Simple Queue Service (SQS). This class handles
    sending messages to an SQS queue, receiving messages from it, and deleting messages
    from the queue.

    :attr sqs boto3.client: The boto3 SQS client.
    :attr request_queue_url str: URL of the SQS queue to which archive requests are sent.
    :attr completion_queue_url str: URL of the SQS queue from which completion messages are received.
    :attr validator Validator: The validator object used to validate messages against a schema.
    """

    def __init__(self, config, validator):
        """
        Initializes a new instance of the SQSArchiveClient with given configuration and validator.

        :param config dict: Configuration dictionary containing AWS region, credentials, and SQS queue URLs.
                              Expected keys are 'region', 'aws_access_key_id', 'aws_secret_access_key', 'request_queue_url',
                              and 'completion_queue_url'.
        :param validator MessageValidator: The validator to use for validating messages.
        """
        required_keys = [
            "region",
            "aws_access_key_id",
            "aws_secret_access_key",
            "request_queue_url",
            "completion_queue_url",
        ]

        # This is to replace the KeyError exception, this fails faster and provides more user feedback
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise ConfigurationException(
                "Missing required configuration keys: %s" % ", ".join(missing_keys)
            )

        self.sqs = boto3.client(
            "sqs",
            region_name=config.get("region"),
            aws_access_key_id=config.get("aws_access_key_id"),
            aws_secret_access_key=config.get("aws_secret_access_key"),
        )
        self.request_queue_url = config.get("request_queue_url")
        self.completion_queue_url = config.get("completion_queue_url")

        self.validator = validator

    def request_archive(self, aipid, filenames, priority="medium"):
        """
        Sends an archive request to the configured SQS request queue.

        :param aipid str: The AIP ID for the archive request.
        :param filenames list: The list of filenames to be archived.
        :param priority str: The priority of the request (default is "medium").

        :return dict: A dictionary containing the response from the SQS service, which includes
                        details such as the message ID and other metadata.
        """
        message = {
            "action": "archive",
            "aipid": aipid,
            "filenames": filenames,
            "priority": priority,
            "timestamp": datetime.now().isoformat(),
        }
        message_json = json.dumps(message)
        message_group_id = "archive-" + aipid
        try:
            response = self.sqs.send_message(
                QueueUrl=self.request_queue_url,
                MessageBody=message_json,
                MessageGroupId=message_group_id,
            )
            return response
        except ClientError as e:
            logger.error(
                "Failed to send archive request for AIP ID {}: {}".format(aipid, str(e))
            )
            raise SQSException(
                e, message="Failed to send archive request for AIP ID {}.".format(aipid)
            )

    def receive_completion_message(self):
        """
        Receives a completion message from the configured SQS completion queue.

        :return dict: A dictionary representing the message received from SQS, which may include
                        the message body and receipt handle among other details.
        """
        try:
            max_messages = int(
                self.config.get("max_number_of_messages", DEFAULT_MAX_MESSAGES)
            )
        except ValueError:
            raise ConfigurationException("Invalid value for max_number_of_messages")

        try:
            wait_time_seconds = int(
                self.config.get("wait_time_seconds", DEFAULT_WAIT_TIME)
            )
        except ValueError:
            raise ConfigurationException("Invalid value for wait_time_seconds")

        try:
            response = self.sqs.receive_message(
                QueueUrl=self.completion_queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_time_seconds,
            )
            if "Messages" in response:
                for msg in response["Messages"]:
                    message_body = json.loads(msg["Body"])
                    try:
                        self.validator.validate(message_body)
                        return message_body
                    except ValidationError as ve:
                        logger.error("Message validation failed: {}".format(str(ve)))
                        raise ValidationException(
                            "Message validation failed.", errors=[str(ve)]
                        )
            return None
        except (
            ClientError,
            NoCredentialsError,
            PartialCredentialsError,
            ParamValidationError,
        ) as e:
            logger.error("Failed to receive completion message: {}".format(str(e)))
            raise SQSException(e, message="Failed to receive completion message.")

    def delete_message(self, receipt_handle):
        """
        Deletes a message from the configured completion SQS queue using the provided receipt handle.

        :param receipt_handle str: The receipt handle of the message to be deleted.

        :return str: Confirmation message noting the deletion of the receipt handle.
        :raises ClientError: If the SQS service reports a client error, especially if the queue does not exist.
        """
        try:
            self.sqs.delete_message(
                QueueUrl=self.completion_queue_url, ReceiptHandle=receipt_handle
            )
            logger.info(
                "Deleted message with receipt handle: {}".format(receipt_handle)
            )
        except ClientError as e:
            logger.error("Failed to delete message from SQS: {}".format(str(e)))
            raise SQSException(
                e,
                message="Failed to delete message receipt handle {} from SQS".format(
                    receipt_handle
                ),
            )
