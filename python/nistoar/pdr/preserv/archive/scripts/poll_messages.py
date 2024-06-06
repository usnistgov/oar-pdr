import json
import logging
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

# This is to be able to import modules from the archive package
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from archive.client import SQSArchiveClient
from archive.validators import JSONSchemaValidator
from dotenv import load_dotenv


def init_logging():
    """
    Initialize logging. Logs are written to `logs/sqs_messages.log`.
    """
    logging.basicConfig(
        level=logging.INFO,
        filename="logs/sqs_messages.log",
        format="%(asctime)s - %(levelname)s - PID: %(process)d - %(message)s",
    )


# Configuration to be loaded either from this local variable or a file
def get_default_config():
    return {
        "request_queue_url": os.getenv("SQS_REQUEST_QUEUE_URL"),
        "completion_queue_url": os.getenv("SQS_COMPLETION_QUEUE_URL"),
        "region": os.getenv("AWS_REGION"),
        "schema_file": os.getenv("SCHEMA_FILE"),
        "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
        "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "max_number_of_messages": os.getenv("MAX_NUMBER_OF_MESSAGES", 1),
        "wait_time_seconds": os.getenv("WAIT_TIME_SECONDS", 20),
    }


def get_schema_path(relative_path):
    """
    Constructs a full path to the schema file.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Root
    return os.path.join(base_dir, relative_path)


def load_config(source="variable", filename=None, url=None):
    """
    Load configuration based on the source parameter.

    :param source: The source type ('variable', 'file', or 'http').
    :param filename: The path to the configuration file (required if source is 'file').
    :param url: The URL to fetch the configuration from (required if source is 'http').
    :return: A configuration dictionary.
    """
    if source == "variable":
        # Load from the local variable
        logging.info("Loading configuration from local variable.")
        return get_default_config()
    elif source == "file":
        if filename is None:
            raise ValueError("A filename must be provided.")
        logging.info(f"Loading configuration from file: {filename}")
        try:
            with open(filename, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            logging.error("Configuration file not found.")
            raise
        except json.JSONDecodeError:
            logging.error("Configuration file is not a valid JSON.")
            raise
    elif source == "http":
        if url is None:
            raise ValueError("A URL must be provided.")
        logging.info(f"Loading configuration from URL: {url}")
        try:
            import requests

            response = requests.get(url)
            response.raise_for_status()  # This will raise an HTTPError of bad response
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Failed to load configuration from URL: {e}")
            raise
    else:
        raise ValueError("Unknown configuration source specified.")


def handle_message(message_content):
    """
    Launch a subprocess to process each validated message.

    This function calls an external Python script (`process_message.py`) to process each message.
    It passes the message content as input to the script.

    :param message_content: The conent of the validated message.
    """
    logging.info(f"Handling message with AIP ID: {message_content['aipid']}")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, "process_message.py")
    message_data = json.dumps(message_content)

    # Command including the aipid argument.
    # The aipid argument here serves as a placeholder only for monitoring purposes.
    command = ["python", script_path, f"--aipid={message_content['aipid']}"]

    # Launch process as a system call
    try:
        subprocess.run(command, input=message_data, text=True, check=True)
        logging.info("Subprocess executed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Subprocess failed with {e.returncode}, error: {e}")


def poll_messages(client):
    """
    Poll for messages and process them asynchronously.
    """
    logging.info("Polling for messages...")
    response = client.receive_completion_message()
    messages = response.get("Messages", [])
    if messages:
        logging.info(f"Received {len(messages)} messages.")
        process_messages_async(messages)
    else:
        logging.info("No messages received.")


def process_messages_async(messages):
    """
    Process messages asynchronously.
    """
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(handle_message, json.loads(message["Body"]))
            for message in messages
        ]
        for future in futures:
            future.result()


def main():
    init_logging()

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Root
    dotenv_path = os.path.join(root_dir, ".env")  # Path to .env file
    # Load environment variables from the .env file
    load_dotenv(dotenv_path)

    config = load_config(source="variable")  # Load default configuration
    schema_path = config["schema_file"]

    # Get the absolute path if not already absolute
    if not os.path.isabs(schema_path):
        schema_path = os.path.join(root_dir, schema_path)
    logging.info(f"Using schema file at: {schema_path}")
    validator = JSONSchemaValidator(schema_path)
    client = SQSArchiveClient(config, validator)
    poll_messages(client)


if __name__ == "__main__":
    main()
