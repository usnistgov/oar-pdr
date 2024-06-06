import argparse
import json
import os
import logging
from client import SQSArchiveClient
from datetime import datetime, timezone

LOG_FILE = "logs/sqs_messages.log"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     filename=LOG_FILE,
#     format="%(asctime)s - %(levelname)s - %(message)s",
# )


def send_message(client, aipid, filenames):
    """Construct and send a message to the SQS queue."""
    message_dict = {
        "action": "archive",
        "aipid": aipid,
        "filenames": filenames,
        "timestamp": datetime.now(timezone.utc).isoformat(),  # ISO 8601 format
        "priority": "low",
    }
    logging.info(
        f"Sending request message to archive AIP ID {aipid} with filenames {filenames}"
    )
    try:
        response = client.send_archive_request(message_dict)
        logging.info(f"Request message sent. SQS response: {response}")
    except Exception as e:
        logging.error(f"Failed to send message due to: {e}")
        raise


def receive_message(client):
    """Receive a message from the SQS queue."""
    logging.info("Receiving message from the SQS queue.")
    response = client.receive_completion_message()
    logging.info(f"Message received: {response}")


def setup_logging(level):
    """Setup logging configuration."""

    # Set logging level based on a user input
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")

    logging.basicConfig(
        level=numeric_level,
        filename=LOG_FILE,
        format=LOG_FORMAT,
    )


def load_config(profile=None):
    """Load configuration from a specified profile in the config directory."""
    default_profile = "local"
    profile = profile or default_profile
    config_path = f"config/config.{profile}.json"

    if not os.path.exists(config_path):
        logging.error(
            f"No configuration file found for the profile '{profile}' at '{config_path}'"
        )
        raise FileNotFoundError(
            f"No configuration file found for the profile '{profile}' at '{config_path}'"
        )

    logging.info(f"Loading configuration from {config_path}")
    with open(config_path, "r") as file:
        return json.load(file)


def create_client(config):
    """Create an SQSArchiveClient instance from configuration."""
    logging.info("Creating an SQS client with the provided configuration.")
    return SQSArchiveClient(config)


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

    subparsers = parser.add_subparsers(dest="command", help="Commands", required=True)

    # Subparser for sending messages
    send_parser = subparsers.add_parser("send", help="Send a message to the queue")
    send_parser.add_argument("--aipid", type=str, required=True, help="AIP identifier")
    send_parser.add_argument(
        "--filenames", nargs="+", required=True, help="List of filenames to be archived"
    )
    send_parser.set_defaults(func=send_message)

    # Subparser for receiving messages
    receive_parser = subparsers.add_parser(
        "receive", help="Receive a message from the queue"
    )
    receive_parser.set_defaults(func=receive_message)

    args = parser.parse_args()
    setup_logging(args.log_level)
    config = load_config(args.profile)
    client = create_client(config)

    try:
        args.func(client, **vars(args))
    except Exception as e:
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
