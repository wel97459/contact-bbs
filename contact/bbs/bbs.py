import logging
import time

from meshtastic import BROADCAST_NUM

from utilities.db_handler import (
    save_message_to_db,
    maybe_store_nodeinfo_in_db,
    get_name_from_database,
    update_node_info_in_db,
    get_nodeid_from_database
)

from bbs.db_operations import initialize_database
from bbs.utils import (
    bbs_send_message,
    get_function
)

user_states = {}

class FindNode:
    def __init__(self, short_name):
        self.user_id = None
        self.short_name = short_name
        self.long_name = None

class BSSContext:
    def __init__(self, currentClass, subFunction, user_id):
        self.currentClass = currentClass
        self.classStack = []
        self.subFunction = subFunction
        self.message = ""
        self.user_id = user_id
        self.tmp = None

class MailMenu:
    def __init__(self):
        pass

    def findNode(context, choice, packet):
        context.message = "Enter short name of node:"
        msg = get_message(packet)
        if len(msg) > 1 and context.tmp:
            res = get_nodeid_from_database(context.tmp.short_name)
            i = int(msg) -1
            if i >=0 and i <= len(res):
                ontext.tmp.user_id = res[i][0]
                context.tmp.long_name = res[i][1]
                context.message = f"Selected node: {context.tmp.user_id}, {context.tmp.short_name}, {context.tmp.long_name}"
                return
        elif len(msg) > 1:
            res = get_nodeid_from_database(msg)
            logging.info(f"get_nodeid_from_database: {res}")
            context.tmp = FindNode(msg)
            if len(res) > 1:
                context.message = "There are multiple nodes with that short name. Which one would you like to leave a message for?\n\n"
                for i, node in enumerate(res):
                    context.message += f"{i+1}. {node[1]}\n"
                return
            else:
                context.tmp.user_id = res[0][0]
                context.tmp.long_name = res[0][1]
                context.message = f"Selected node: {context.tmp.user_id}, {context.tmp.short_name}, {context.tmp.long_name}"

    def main(context, choice, packet):
        match choice:
            case "x":
                user_state_popClass(context, packet)
                return
            case "s":
                user_state_changeFunction(context, "findNode", packet)
                return

        context.message = "📪 Mail Menu\n\n"
        context.message += "[R]ead\n"
        context.message += "[S]end\n"
        context.message += "E[X]it\n"

class MainMenu:
    def __init__(self):
        pass

    def main(context, choice, packet):
        match choice:
            case "b":
                return
            case "m":
                user_state_pushClass(context, MailMenu, packet)
                return
            case "u":
                return

        context.message = "🚧 This BBS is a Work In Progress 🚧\n\n"
        context.message += "📰BBS Menu📰\n\n"
        context.message += "[B]ulletins\n"
        context.message += "[M]ail\n"
        context.message += "[U]tilities\n"

def user_state_popClass(state, packet):
    if state.classStack:
        state.message = ""
        state.subFunction = "main"
        state.currentClass = state.classStack.pop()
        get_function(state.currentClass, state.subFunction, state, "", packet)

def user_state_pushClass(state, newClass, packet):
    state.message = ""
    state.subFunction = "main"
    state.classStack.append(state.currentClass)
    state.currentClass = newClass
    get_function(state.currentClass, state.subFunction, state, "", packet)

def user_state_changeFunction(state, newFunction, packet):
    state.message = ""
    state.subFunction = newFunction
    get_function(state.currentClass, state.subFunction, state, "", packet)

def update_user_state(user_id, state):
    user_states[user_id] = state
    return state

def get_user_state(user_id):
    state = user_states.get(user_id, None)
    if state == None:
        return update_user_state(user_id, BSSContext(MainMenu, "main", user_id))
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
    choice = get_user_choice(get_message(packet))
    get_function(state.currentClass, state.subFunction, state, choice, packet)
    return state

def bbs_main():
    initialize_database()

def on_receive_bbs(packet):
    context = call_user_state(packet["from"], packet)
    bbs_send_message(context.message , packet["from"])
    logging.info(f"Packet: {packet}")