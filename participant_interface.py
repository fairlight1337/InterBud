# This interface defines what methods a chat participant class should implement.
# It is initialized with a label (name) and a callback function that will be called
# to add new messages to the chat history. Also, it needs to implement a send_message
# method that will be called by the chat app to send a message to the chat participant.
# The data in this call will contain (datetime, sender, message). It also needs to implement
# a method that is called when the currently typed text by the participant changes
# (e.g., when a keyboard user types, with each keystroke this function is called with
# the current text in the input field). This method should be used to update the input
# field in the chat frontend.
class ChatParticipantInterface(object):
    def __init__(self, label):
        self.label = label
        self.message_send_callback = None
        self.quit_app_callback = None
        self.update_input_callback = None
        self.should_quit = False

    def register_message_send_callback(self, message_send_callback):
        self.message_send_callback = message_send_callback
    
    def register_quit_app_callback(self, quit_app_callback):
        self.quit_app_callback = quit_app_callback
    
    def register_update_input_callback(self, update_input_callback):
        self.update_input_callback = update_input_callback
    
    def quit(self):
        self.should_quit = True

    def send_message(self, send_datetime, sender, message):
        raise NotImplementedError("Chat participants must implement the send_message method.")