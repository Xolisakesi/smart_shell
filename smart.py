#!/usr/bin/env python3

import subprocess
import sys
import os
import requests

OLLAMA_API_URL = "http://localhost:11434/api/generate"

def translate_to_command(natural_language):
    """Use Ollama with DeepSeek to translate natural language into a CLI command."""
    current_directory = os.getcwd()
    
    # Stricter prompt to force only command output
    prompt = (
        f"You are a Linux terminal. The current working directory is: {current_directory}. "
        f"Translate the following natural language into a Linux command. "
        f"ONLY return the command itself. DO NOT provide explanations, descriptions, or reasoning. "
        f"DO NOT include additional text, markdown, or formatting. Respond with a single-line command: {natural_language}"
    )

    payload = {
        "model": "deepseek-r1:1.5b",
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(OLLAMA_API_URL, json=payload)

    if response.status_code == 200:
        raw_response = response.json().get("response", "").strip()

        # Ensure response contains only a single valid command
        command_lines = [line.strip() for line in raw_response.split("\n") if line and not line.startswith("<")]

        if command_lines:
            return command_lines[0]  # Return only the first valid command
        else:
            raise Exception(f"Invalid response from AI: {raw_response}")
    else:
        raise Exception(f"Failed to translate: {response.text}")

def execute_command(command):
    """Execute the CLI command in the current shell environment."""
    try:
        result = subprocess.run(command, shell=True, check=True, executable="/bin/bash", text=True, capture_output=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e.stderr}")

def main():
    if len(sys.argv) < 2:
        print("Usage: smart_terminal <natural language command>")
        sys.exit(1)

    user_input = " ".join(sys.argv[1:])

    try:
        command = translate_to_command(user_input)
        print(f"Executing command: {command}")
        execute_command(command)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

