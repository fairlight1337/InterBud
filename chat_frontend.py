import curses
import queue

class ChatFrontend:
    def __init__(self, stdscr):
        self.message_queue = queue.Queue()
        self.running = False
        self.last_input_text = ""

        # Initialize curses
        self.stdscr = stdscr
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)

        # Create two sub-windows: One that displays chat history and one for user input
        self.height, self.width = self.stdscr.getmaxyx()
        self.history_height = self.height - 3
        self.history_width = self.width
        self.input_height = 3
        self.input_width = self.width
        self.history_start_y = 0
        self.history_start_x = 0
        self.input_start_y = self.height - 3
        self.input_start_x = 0

        # Create history pad
        self.history_pad = curses.newpad(1000, self.history_width)  # Large height for the pad to allow scrolling
        self.history_pad.scrollok(True)
        self.history_pad.idlok(True)

        # Create history window border
        self.history_win = curses.newwin(self.history_height, self.history_width, self.history_start_y, self.history_start_x)
        self.history_win.border()

        # Create input window
        self.input_win = curses.newwin(self.input_height, self.input_width, self.input_start_y, self.input_start_x)
        self.input_win.border()
        self.input_win.move(1, 2)
        self.input_win.addstr("> ")

        # Refresh the main window and sub-windows
        self.stdscr.refresh()
        self.history_win.refresh()
        self.input_win.refresh()

        self.history_cursor_y = 1  # Start cursor position for history pad
        self.history_pad_offset = 0

    def split_string_into_chunks(self, text, max_length=40):
        words = text.split()
        chunks = []
        current_chunk = []

        for word in words:
            if len(word) > max_length:
                # If a single word is longer than the max length, split it forcefully
                for i in range(0, len(word), max_length):
                    chunks.append(word[i:i+max_length])
            else:
                # Check if adding the word would exceed the max length
                if sum(len(w) for w in current_chunk) + len(current_chunk) + len(word) <= max_length:
                    current_chunk.append(word)
                else:
                    # Add the current chunk to the list and start a new chunk
                    chunks.append(' '.join(current_chunk))
                    current_chunk = [word]

        # Add the last chunk if there are any words left
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def run(self):
        self.running = True

        while self.running:
            # If there are messages in the queue (format (datetime, sender, message)), add them to
            # the chat history pad.
            try:
                date, sender, message = self.message_queue.get(timeout=1)
                if message:
                    lines = message.split('\n')
                    for line in lines:
                        chunks = self.split_string_into_chunks(line, 160)
                        for chunk in chunks:
                            self.history_pad.addstr(self.history_cursor_y, 1, f"[{date.strftime('%H:%M:%S')}] {sender}: {chunk}")
                            self.history_cursor_y += 1
                            if self.history_cursor_y >= self.history_height - 1:
                                self.history_pad_offset += 1
                        self.history_pad.refresh(self.history_pad_offset, 0, self.history_start_y + 1, self.history_start_x + 1, self.history_start_y + self.history_height - 2, self.history_start_x + self.history_width - 2)

                    self.update_input("", self.last_input_text)
            except queue.Empty:
                continue
    
    def quit(self):
        self.running = False
    
    def enqueue_message(self, date, sender, message):
        self.message_queue.put((date, sender, message))
    
    def update_input(self, label, text):
        self.last_input_text = text
        self.input_win.clear()
        self.input_win.border()
        self.input_win.move(1, 2)
        self.input_win.addstr(f"> {text}")
        self.input_win.refresh()
