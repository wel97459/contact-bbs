import logging
import time

from meshtastic import BROADCAST_NUM

from bbs.db_operations import initialize_database
from bbs.utils import (
    bbs_send_message,
    get_function
)

user_states = {}

class BSSContext:
    def __init__(self, currentClass, subFunction):
        self.currentClass = currentClass
        self.lastClass = None
        self.subFunction = subFunction
        self.message = ""

class MainMenu:
    def __init__(self):
        pass

    def main(context, packet):
        context.message = "BBS is a Work In Progress\n\n"
        context.message += "📰BBS Menu📰\n\n"
        context.message += "[B]ulletins\n"
        context.message += "[M]ail\n"
        context.message += "[U]tilities\n"
        bbs_send_message(context.message , packet["from"])
        logging.info(f"User choice: {get_user_choice(get_message(packet))}")

def update_user_state(user_id, state):
    user_states[user_id] = state
    return state

def get_user_state(user_id):
    state = user_states.get(user_id, None)
    if state == None:
        return update_user_state(user_id, BSSContext(MainMenu, "main"))
    return state

def get_message(packet):
    message_bytes = packet["decoded"]["payload"]
    return message_bytes.decode("utf-8")

def get_user_choice(message):
    message = message.lower().strip()
    if len(message) == 2 and message[1] == 'x':
        message = message[0]
    return message

def call_user_state(user_id, packet):
    state = get_user_state(user_id)
    get_function(state.currentClass, state.subFunction, state, packet)

def bbs_main():
    initialize_database()

def on_receive_bbs(packet):
    context = call_user_state(packet["from"], packet)

    #bbs_send_message("This BBS is a WIP.", packet["from"])
    #logging.info(f"on_receive_bbs: {packet["from"]}")

def test_function():
    logging.info("Testing")