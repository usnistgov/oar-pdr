#!/usr/bin/python
import argparse
import json
import logging
import sys
import os

# Current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add the root directory to PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(current_dir, "../../..")))

from nistoar.pdr.preserv.archive.client import SQSArchiveClient
from nistoar.pdr.preserv.archive.validators import JSONSchemaValidator

LOG_FILE = os.path.join(current_dir, "logs", "sqs_cli.log")
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


# Configure logging
def setup_logging(level):
    """Setup logging configuration."""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError("Invalid log level: {}".format(level))

    logging.basicConfig(
        level=numeric_level,
        filename=LOG_FILE,
        format=LOG_FORMAT,
    )


def load_config(profile=None):
    """Load configuration from a specified profile in the config directory."""
    default_profile = "local"
    profile = profile or default_profile
    config_path = os.path.join(current_dir, "config", "config.{}.json".format(profile))

    if not os.path.exists(config_path):
        logging.error(
            "No configuration file found for the profile '{}' at '{}'".format(
                profile, config_path
            )
        )
        raise IOError(
            "No configuration file found for the profile '{}' at '{}'".format(
                profile, config_path
            )
        )

    logging.info("Loading configuration from {}".format(config_path))
    with open(config_path, "r") as file:
        return json.load(file)


def create_client(config):
    """Create an SQSArchiveClient instance from configuration."""
    logging.info("Creating an SQS client with the provided configuration.")
    validator = JSONSchemaValidator(config.get("schema_file"))
    return SQSArchiveClient(config, validator)


def send_message(client, aipid, filenames):
    """Construct and send a message to the SQS queue."""
    logging.info(
        "Sending request message to archive AIP ID {} with filenames {}".format(
            aipid, filenames
        )
    )
    try:
        response = client.request_archive(aipid, filenames)
        logging.info("Request message sent. SQS response: {}".format(response))
    except Exception as e:
        logging.error("Failed to send message due to: {}".format(e))
        raise


def receive_message(client):
    """Receive a message from the SQS queue."""
    logging.info("Receiving message from the SQS queue.")
    try:
        message = client.receive_completion_message()
        logging.info("Message received: {}".format(message))
    except Exception as e:
        logging.error("Failed to receive message due to: {}".format(e))
        raise


def delete_message(client, receipt_handle):
    """Delete a message from the SQS queue using the receipt handle."""
    logging.info("Deleting message with receipt handle {}".format(receipt_handle))
    try:
        client.delete_message(receipt_handle)
        logging.info("Message deleted successfully.")
    except Exception as e:
        logging.error("Failed to delete message due to: {}".format(e))
        raise


def main():
    parser = argparse.ArgumentParser(
        description="CLI for interacting with SQS via the SQSArchiveClient."
    )
    parser.add_argument(
        "--profile", type=str, help="Configuration profile to use", default="local"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Set the logging level (e.g., DEBUG, INFO)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Subparser for sending messages
    send_parser = subparsers.add_parser("send", help="Send a message to the queue")
    send_parser.add_argument("--aipid", type=str, required=True, help="AIP identifier")
    send_parser.add_argument(
        "--filenames", nargs="+", required=True, help="List of filenames to be archived"
    )

    # Subparser for receiving messages
    receive_parser = subparsers.add_parser(
        "receive", help="Receive a message from the queue"
    )

    # Subparser for deleting messages
    delete_parser = subparsers.add_parser(
        "delete", help="Delete a message from the queue"
    )
    delete_parser.add_argument(
        "--receipt-handle",
        type=str,
        required=True,
        help="Receipt handle of the message to delete",
    )

    args = parser.parse_args()
    setup_logging(args.log_level)
    config = load_config(args.profile)
    client = create_client(config)

    if args.command == "send":
        send_message(client, args.aipid, args.filenames)
    elif args.command == "receive":
        receive_message(client)
    elif args.command == "delete":
        delete_message(client, args.receipt_handle)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
