from participant_interface import ChatParticipantInterface

from datetime import datetime
import curses
import threading

# Keyboard chat participant. This class is used to represent a chat participant that
# sends messages based on keyboard input. It is initialized with a label (name) and
# a callback function that will be called to add new messages to the chat history.
# Its 'send_message' method does nothing as the user sees the chat history in the respective
# chat frontend window. The 'update_input' method is called when the user types in the
# chat input field. This method should be used to update the input field in the chat frontend.
# This class spawns a thread that listens for keyboard input and sends it to the chat frontend.
# CTRL-D is used to exit the chat. When the user hits <Enter>, the current text in the input
# field is sent to the chat frontend.
class KeyboardChatParticipant(ChatParticipantInterface):
    def __init__(self, label, stdscr):
        self.label = label
        self.running = False
        self.input_text = ""
        self.stdscr = stdscr
        self.update_input_callback = None
        self.message_send_callback = None
        self.quit_app_callback = None
    
    def send_message(self, send_datetime, sender, message):
        pass
    
    def update_input(self, text):
        self.input_text = text
        if self.update_input_callback:
            self.update_input_callback(self.label, text)
    
    def quit(self):
        self.running = False

    def run(self):
        self.running = True

        def keyboard_thread():
            while self.running:
                char = self.stdscr.get_wch()
                if char == chr(4):  # CTRL-D
                    self.running = False
                    if self.quit_app_callback:
                        self.quit_app_callback()
                    break
                elif char == '\n':
                    user_input = self.input_text
                    self.input_text = ""
                    if user_input:
                        if self.message_send_callback:
                            self.update_input(self.input_text)
                            self.message_send_callback(datetime.now(), self.label, user_input)
                elif char == curses.KEY_BACKSPACE or char == '\b' or char == 127:
                    self.input_text = self.input_text[:-1]
                    self.update_input(self.input_text)
                elif isinstance(char, str):
                    self.update_input(self.input_text + char)
        
        self.thread = threading.Thread(target=keyboard_thread)
        self.thread.start()