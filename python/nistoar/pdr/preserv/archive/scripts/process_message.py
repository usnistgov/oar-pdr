import sys
import json
import logging
import argparse
import time


def process_message(message_data, aipid):
    logging.basicConfig(
        level=logging.INFO,
        filename="logs/sqs_messages.log",
        format="%(asctime)s - %(levelname)s - PID: %(process)d - %(message)s",
    )
    try:
        # Parse the JSON content from the 'Body' key
        message_content = json.loads(message_data)

        # Example of accessing keys
        action = message_content["action"]
        filenames = message_content["filenames"]

        # Logging the processing of the message with additional aipid info from command-line
        logging.info(
            f"Processing message for AIP ID: {aipid} with action {action} on files {filenames}"
        )

        # Process message logic here
        time.sleep(30)
    except json.JSONDecodeError as e:
        logging.error("Decoding JSON failed")
    except KeyError as e:
        logging.error("Missing expected key in message")
    except Exception as e:
        logging.error(f"An error occurred: {e}")


def main():
    parser = argparse.ArgumentParser(description="Process a message")
    parser.add_argument("--aipid", required=True, help="AIP ID for the process")
    args = parser.parse_args()

    input_data = sys.stdin.read()  # Read input from stdin
    process_message(input_data, args.aipid)


if __name__ == "__main__":
    main()
