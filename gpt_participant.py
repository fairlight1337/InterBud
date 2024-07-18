from openai import OpenAI

import queue
import threading
from datetime import datetime
from participant_interface import ChatParticipantInterface
from pathlib import Path
import json
import subprocess

class GptParticipant(ChatParticipantInterface):
    def __init__(self, label, api_key, model="gpt-4o-mini", base_file_folder=Path("gpt_managed_files/")):
        super(GptParticipant, self).__init__(label)

        # Ensure the base file folder exists
        base_file_folder.mkdir(parents=True, exist_ok=True)

        self.client = OpenAI(api_key=api_key)
        self.api_key = api_key
        self.model = model
        self.running = False
        self.message_queue = queue.Queue()

        self.messages = [{"role": "system", "content": "You are a helpful assistant. You have access to a Ubuntu Linux system, can run shell commands and interact with the file system. You assist the user in any way they require help."}]

        self.base_file_folder = base_file_folder

    def run_command_in_directory(self, command, working_directory):
        """
        Runs a command in a specified working directory and returns the output.

        Parameters:
        - command: list of str, the command and its arguments to run.
        - working_directory: str or Path, the directory in which to run the command.

        Returns:
        - str: The standard output from the command.
        """
        try:
            process = subprocess.Popen(command, cwd=working_directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, command, output=stdout, stderr=stderr)
            
            return stdout
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}"
        except Exception as e:
            return f"An error occurred: {e}"
    
    def run_command(self, command, relative_path):
        """
        Runs a command in the current working directory and returns the output.

        Parameters:
        - command: list of str, the command and its arguments to run.
        - relative_path: str, the path relative to the base file folder to run the command in.

        Returns:
        - str: The standard output from the command.
        """
        return self.run_command_in_directory(command, self.base_file_folder / Path(relative_path))

    def list_folder(self, relative_folder):
        path = self.base_file_folder / Path(relative_folder)
        if not path.exists():
            return json.dumps({'status': 'error', 'message': f'Path "{relative_folder}" does not exist'})

        if not path.is_dir():
            return json.dumps({'status': 'error', 'message': f'Path "{relative_folder}" is not a directory'})

        contents = {'files': [], 'folders': []}
        for item in path.iterdir():
            if item.is_file():
                contents['files'].append(item.name)
            elif item.is_dir():
                contents['folders'].append(item.name)

        return json.dumps(contents)

    def read_file(self, relative_path):
        path = self.base_file_folder / Path(relative_path)
        if not path.exists():
            return json.dumps({'status': 'error', 'message': f'Path "{relative_path}" does not exist'})

        if path.is_dir():
            return json.dumps({'status': 'error', 'message': f'Path "{relative_path}" is not a file'})

        return path.read_text()

    def write_file(self, relative_path, contents):
        path = self.base_file_folder / Path(relative_path)
        # Create all directories in the path if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)
        return "Write successful."
    
    def create_directory(self, relative_path):
        path = self.base_file_folder / Path(relative_path)
        if path.exists() and not path.is_dir():
            return json.dumps({'status': 'error', 'message': f'Path "{relative_path}" exists but is a file'})

        path.mkdir(parents=True, exist_ok=True)
        return "Directory created."

    def send_message(self, send_datetime, sender, message):
        self.message_queue.put((send_datetime, sender, message))

    def _process_messages(self, messages):
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "list_folder",
                    "description": "Get a JSON object containing the folders and files inside a path relative to the base folder.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_folder": {
                                "type": "string",
                                "description": "The folder to list, relative to the base folder.",
                            },
                        },
                        "required": ["relative_folder"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Get a contents of a file at a path relative to the base folder.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_path": {
                                "type": "string",
                                "description": "The file to read, relative to the base folder.",
                            },
                        },
                        "required": ["relative_path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write contents to a file at a path relative to the base folder",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_path": {
                                "type": "string",
                                "description": "The file to write, relative to the base folder.",
                            },
                            "contents": {
                                "type": "string",
                                "description": "The contents to write to the file.",
                            },
                        },
                        "required": ["relative_path", "contents"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_directory",
                    "description": "Create a directory at a path relative to the base folder.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_path": {
                                "type": "string",
                                "description": "The directory to create, relative to the base folder.",
                            },
                        },
                        "required": ["relative_path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "run_command",
                    "description": "Run a Ubuntu Linux shell command in the folder given relative to the base folder.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The command to execute.",
                            },
                            "relative_path": {
                                "type": "string",
                                "description": "The folder to run the command in, relative to the base folder.",
                            },
                        },
                        "required": ["command", "relative_path"],
                    },
                },
            }
        ]

        try:
            for message in messages:
                self.messages.append(message)
            response = self.client.chat.completions.create(model=self.model, messages = self.messages, tools=tools)
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            self.messages.append(response_message)
            if tool_calls:
                available_functions = {
                    "list_folder": self.list_folder,
                    "read_file": self.read_file,
                    "write_file": self.write_file,
                    "create_directory": self.create_directory,
                }
                tool_call_results = []
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_to_call = available_functions.get(function_name)
                    function_args = json.loads(tool_call.function.arguments)
                    if self.message_send_callback:
                        self.message_send_callback(datetime.now(), self.label, f"Calling function {function_name} with arguments {function_args}")
                    if function_name == "list_folder":
                        function_response = function_to_call(
                            relative_folder=function_args.get("relative_folder"),
                        )
                    elif function_name == "read_file":
                        function_response = function_to_call(
                            relative_path=function_args.get("relative_path"),
                        )
                    elif function_name == "write_file":
                        function_response = function_to_call(
                            relative_path=function_args.get("relative_path"),
                            contents=function_args.get("contents"),
                        )
                    elif function_name == "create_directory":
                        function_response = function_to_call(
                            relative_path=function_args.get("relative_path"),
                        )
                    elif function_name == "run_command":
                        function_response = self.run_command(
                            command=function_args.get("command").split(),
                            relative_path=function_args.get("relative_path"),
                        )

                    tool_call_results.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": function_response,
                        }
                    )
                
                return self._process_messages(tool_call_results)
            else:
                return response_message.content
        except Exception as e:
            return f"Error: {e}" + str(self.messages)

    def run(self):
        self.running = True
        def gpt_thread():
            while self.running:
                try:
                    send_datetime, sender, message = self.message_queue.get(timeout=1)
                    response = self._process_messages([{"role": "user", "content": message}])
                    if response:
                        if self.message_send_callback:
                            self.message_send_callback(datetime.now(), self.label, response)
                except queue.Empty:
                    continue

        self.thread = threading.Thread(target=gpt_thread)
        self.thread.start()

    def quit(self):
        self.running = False
        self.thread.join()