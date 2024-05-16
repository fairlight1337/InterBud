#!/usr/bin/env python3

import argparse
import curses
from interbud_app import InterBudApp

def main(stdscr, openai_api_key):
    app = InterBudApp(stdscr, openai_api_key)
    app.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='InterBud chat frontend')
    parser.add_argument('--openai_api_key', help='OpenAI API key', required=True)
    args = parser.parse_args()

    openai_api_key = args.openai_api_key
    curses.wrapper(main, openai_api_key)