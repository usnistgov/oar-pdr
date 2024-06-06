# SQS Archive Client

This package contains Python scripts and modules designed to interact with AWS SQS for archiving purposes. The system includes components for sending messages to an SQS queue, polling messages from the queue, and processing those messages based on a specific message schema.

## Components

### AbstractArchiveClient

An abstract base class for implementing various archive clients.

### SQSArchiveClient

An implementation of the `AbstractArchiveClient` that interacts with AWS SQS to send and receive messages.

### MockArchiveClient

A mock implementation of the `AbstractArchiveClient` for testing purposes without actual AWS SQS communication.

### CLI Program

A command-line interface program that configures an `SQSArchiveClient` to send formatted messages to the SQS request queue.

### process_message.py

A script used to process messages retrieved from the SQS queue. It handles each message according to the specified schema and performs necessary archive operations.

### poll_messages.py

A script that continuously polls the SQS queue for new messages and uses `process_message.py` to process each message.




## Usage

### Sending Messages

Before running the CLI, set up these environment variables:

- `AWS_ACCESS_KEY_ID`: AWS access key.
- `AWS_SECRET_ACCESS_KEY`: AWS secret access key.
- `AWS_REGION`: AWS region.
- `SQS_REQUEST_QUEUE_URL`: URL of the SQS request queue.
- `SQS_COMPLETION_QUEUE_URL`: URL of the SQS completion queue.

Use `export` command or  a `.env` to set them.

To send messages to the SQS queue using the CLI program, run a command similar to the following:

```sh
python cli.py --profile local send --aipid "mds2909" --filenames "trial1.txt" "trial2.txt"
```

- `--profile local`: specifies which configuration profile to use. In this case, local is the profile name, which points to specific configurations suitable for a local dev inside the `config` directory.

- `send`: a subcommand of `cli.py`. It is used to send a message to the configured **request** queue. The CLI program also supports a `receive` subcommand for receiving messages from the **completion** queue. 

- `--aipid "mds2909"`: specifies the Archive Information Package Identifier (AIP ID).

- `--filenames "trial1.txt" "trial2.txt"`: specifies the filenames to be included in the message sent to SQS. This `filenames` option might be used to identify specific files to be archived. This will also depend on the receiver, who will decide what to do with the filenames list.

## Scripts

### poll_messages.py

This script polls an AWS SQS queue for messages, validates them against a predefined JSON schema, and processes each message asynchronously.

- **Key Functions**:

    - `handle_message()`: processes individual messages by calling an external script (`process_message.py`) via a subprocess (system call), passing the message data and handling subprocess execution.
    - `poll_messages()`: retrieves messages from the SQS queue, handles them based on the validator's response, and manages asynchronous processing of each message using threads.
    - `process_messages_async()`: manages the asynchronous execution of message processing tasks, using Python's `ThreadPoolExecutor` for concurrent processing.

### process_message.py

This script is used to process individual messages based on the data received from `poll_messages.py`, and it is executed as a subprocess.

- **Key Functions**:

    - `process_message()`: takes message data and an AIP ID as input, logs processing details, and performs specified actions based on the message content. This function is designed to be called with command-line arguments specifying the AIP ID and receives the message content via stdin. AIPID here is used as placehoder for monitoring purposes.
    - `main()`: uses `argparser` to accept the AIP ID, reads the message data from stdin, and calls `process_message()` with the appropriate arguments.

### Workflow

- `poll_messages.py` is executed, typically as a cron job, and enters a polling loop where it retrieves messages from an SQS queue; each message is validated against a JSON schema. Valid messages are passed to `process_message.py` for further processing.

- `process_message.py` processes each message in a separate subprocess to ensure that the processing of each message does not block the polling loop.


## Notes

- Make sure that the AWS credentials are set up correctly in the config file.
- Adjust the thread pool size in `poll_messages.py` based on the expected load and system capabilities.
- The logging paths, configurations paths/profiles, and schemas paths may need to be adjusted based on the deployment environment.