from chat_frontend import ChatFrontend
from keyboard_participant import KeyboardChatParticipant
from gpt_participant import GptParticipant

class InterBudApp(object):
    def __init__(self, stdscr, openai_api_key):
        self.stdscr = stdscr
        self.openai_api_key = openai_api_key
        self.frontend = ChatFrontend(stdscr)
        self.chat_participants = {}
    
    def run(self):
        self.add_chat_partner("User", KeyboardChatParticipant("User", self.stdscr))
        self.add_chat_partner("GPT", GptParticipant("GPT", self.openai_api_key, "gpt-4o"))
        self.frontend.run()
    
    def process_message(self, date, sender, message):
        self.frontend.enqueue_message(date, sender, message)
        for participant in self.chat_participants:
            if participant == sender:
                continue
            obj = self.chat_participants[participant]
            obj.send_message(date, sender, message)
    
    def add_chat_partner(self, label, chat_partner):
        self.chat_participants[label] = chat_partner
        chat_partner.register_message_send_callback(self.process_message)
        chat_partner.register_quit_app_callback(self.quit_app)
        chat_partner.register_update_input_callback(self.frontend.update_input)
        chat_partner.run()
    
    def quit_app(self):
        for participant in self.chat_participants:
            self.chat_participants[participant].quit()
        self.frontend.quit()