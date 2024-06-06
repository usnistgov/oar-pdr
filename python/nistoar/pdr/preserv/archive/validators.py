import json
import logging
from abc import ABC, abstractmethod
from urllib.parse import urlparse

import requests
from jsonschema import SchemaError, ValidationError, validate


class MessageValidator(ABC):
    """
    An abstract base class for message validators. Classes that inherit from this must
    implement the validate method to ensure message data matches a schema.
    """

    @abstractmethod
    def validate(self, message):
        """
        Validate the message data.

        :param message dict: The message data to be validated.
        :raises ValidationError: If the message does not meet the validation criteria.
        """
        pass


class JSONSchemaValidator(MessageValidator):
    """
    Validates a message against a JSON schema. The schema can be loaded from a local file or a URL.

    :attr schema dict: The JSON schema against which messages will be validated.
    """

    def __init__(self, schema_source):
        """
        Initializes the JSONSchemaValidator with a schema loaded from a given source.

        :param schema_source str: The file path or URL to the JSON schema file.
        """
        self.schema = self.load_schema(schema_source)

    def load_schema(self, schema_source):
        """
        Loads a JSON schema from a specified file path or URL.

        :param schema_source str: The file path or URL to the JSON schema file.
        :return dict: The loaded JSON schema.
        :raises Exception: If the schema cannot be loaded from the specified source.
        """
        if urlparse(schema_source).scheme in ("http", "https"):
            try:
                response = requests.get(schema_source)
                response.raise_for_status()  # Raises HTTPError for bad responses
                return response.json()
            except requests.RequestException as e:
                raise Exception(f"Failed to load schema from URL: {e}")
        else:
            try:
                with open(schema_source, "r") as file:
                    return json.load(file)
            except FileNotFoundError:
                raise Exception(f"Schema file not found: {schema_source}")
            except json.JSONDecodeError:
                raise Exception("Invalid JSON in schema file.")

    def validate(self, message):
        """
        Validates a message against the loaded JSON schema.

        :param message dict: The message data to validate.
        :raises ValidationError: If the message fails to validate against the schema.
        :raises SchemaError: If the schema itself is invalid.
        """
        try:
            validate(instance=message, schema=self.schema)
            logging.info("Validation successful.")
        except ValidationError as e:
            logging.info(f"Validation failed: {e}")
            raise
        except SchemaError as e:
            logging.info(f"Schema validation error: {e}")
            raise


class AIPIDValidator(MessageValidator):
    """
    Validator with a simple logic; it checks for the presence of an 'aipid' in the message dictionary and raises an
    error if it is missing.
    """

    def validate(self, message):
        """
        Validates that the message contains the 'aipid' key.

        :param message dict: The message data to validate.
        :raises ValidationError: If 'aipid' is missing from the message.
        """
        if "aipid" not in message:
            raise ValidationError("Missing 'aipid' in message.")
        logging.info("Validation successful.")
