#!/usr/bin/python
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
        # Use dict.get() to avoid KeyError for optional fields
        action = message_data.get("action")
        filenames = message_data.get("filenames")

        if action is None:
            logging.error("Missing required key 'action' in message data.")
            return

        if filenames is None:
            logging.info("No 'filenames' key found in message, archiving entire AIP.")

        # Logging the processing of the message with additional aipid info from command-line
        logging.info(
            "Processing message for AIP ID: {} with action {} on files {}".format(
                aipid, action, filenames if filenames else "entire AIP"
            )
        )

        # TODO: process message logic here
        time.sleep(10)
    except json.JSONDecodeError as e:
        logging.error("Decoding JSON failed: {}".format(str(e)))
    except Exception as e:
        logging.error("An error occurred: {}".format(str(e)))


def main():
    parser = argparse.ArgumentParser(description="Process a message")
    parser.add_argument("--aipid", required=True, help="AIP ID for the process")
    args = parser.parse_args()

    input_data = sys.stdin.read()  # Read input from stdin
    message_data = json.loads(input_data)  # Load the input data as JSON
    process_message(message_data, args.aipid)


if __name__ == "__main__":
    main()
