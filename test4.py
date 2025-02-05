#!/usr/bin/env python3

import subprocess
import sys
import os
import requests
import shlex
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OLLAMA_API_URL = "http://localhost:11434/api/generate"

# List of allowed commands and their valid options
ALLOWED_COMMANDS = {
    "ls": ["-l", "-a", "-la", "-lh", "-alh"],
    "cd": [],
    "pwd": [],
    "mkdir": [],
    "rm": ["-r", "-f", "-rf"],
    "mv": [],
    "cp": ["-r"],
    "touch": [],
    "cat": [],
    "grep": ["-i", "-v", "-r"],
    "find": []
}

def translate_to_command(natural_language):
    """Use Ollama with DeepSeek to translate natural language into a CLI command."""
    current_directory = os.getcwd()

    # Stricter prompt to force only command output
    prompt = (
        f"You are a Linux terminal. The current working directory is: {current_directory}. "
        f"Translate the following natural language into a Linux command. "
        f"ONLY return the command itself. DO NOT provide explanations, descriptions, or reasoning. "
        f"DO NOT include additional text, markdown, or formatting. "
        f"DO NOT use placeholders like <think> or <command>. "
        f"Respond with a single-line command that can be executed directly in a Linux terminal. "
        f"Valid commands include: {', '.join(ALLOWED_COMMANDS.keys())}. "
        f"Valid options for 'ls' include: {', '.join(ALLOWED_COMMANDS['ls'])}. "
        f"Example: 'ls -l', 'cd /path', 'mkdir new_folder'. "
        f"Natural language input: {natural_language}"
    )

    payload = {
        "model": "deepseek-r1:1.5b",
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=120)  # Increased timeout
        response.raise_for_status()  # Raise HTTP errors
    except requests.exceptions.Timeout:
        raise Exception("API request timed out. Ensure the Ollama service is running and accessible.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {e}")

    raw_response = response.json().get("response", "").strip()
    logger.info(f"Raw response from model: {raw_response}")  # Print the raw response for debugging

    # Use regex to extract the command
    command_pattern = r"(?:^|\n)([^\n`<>]+)$"
    match = re.search(command_pattern, raw_response)

    if match:
        # Extract the command from the first non-empty group
        command = match.group(1).strip()
        logger.info(f"Extracted command: {command}")
        return command
    else:
        raise Exception(f"No valid command found in response: {raw_response}")

def validate_command(command):
    """Validate the extracted command against a list of allowed commands and options."""
    command_parts = shlex.split(command)
    base_command = command_parts[0]

    if base_command not in ALLOWED_COMMANDS:
        raise Exception(f"Invalid command: {base_command}. Allowed commands are: {', '.join(ALLOWED_COMMANDS.keys())}")

    # Validate options for the command
    if base_command == "ls":
        options = command_parts[1:]
        for opt in options:
            if not opt.startswith("-"):
                continue  # Skip non-option arguments (e.g., directory paths)
            if opt not in ALLOWED_COMMANDS["ls"]:
                raise Exception(f"Invalid option for 'ls': {opt}. Valid options are: {', '.join(ALLOWED_COMMANDS['ls'])}")

    return command

def execute_command(command):
    """Execute the CLI command in the current shell environment."""
    try:
        # Split the command into a list of arguments
        command_args = shlex.split(command)
        logger.info(f"Executing command: {command_args}")
        result = subprocess.run(
            command_args,  # Pass the command as a list of arguments
            check=True,
            text=True,
            capture_output=True
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing command: {e.stderr}")

def main():
    if len(sys.argv) < 2:
        print("Usage: smart_terminal <natural language command>")
        sys.exit(1)

    user_input = " ".join(sys.argv[1:])

    if not user_input.strip():
        logger.error("Error: No input provided.")
        sys.exit(1)

    try:
        command = translate_to_command(user_input)
        validated_command = validate_command(command)
        execute_command(validated_command)
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()
