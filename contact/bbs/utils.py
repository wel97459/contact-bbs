import logging
import time

from meshtastic import BROADCAST_NUM
from message_handlers.tx_handler import send_message, send_traceroute

from utilities.db_handler import get_name_from_database

from ui.contact_ui import (
    select_node_by_id,
    check_channel_exsists
)
from utilities.utils import get_node_channle


def bbs_send_message(message: str, destination: int = BROADCAST_NUM) -> None:
    ch = check_channel_exsists(destination)
    chunks = split_into_chunks(message)
    for i, chunk in enumerate(chunks):
        try:
            d = send_message(chunk, channel = ch)
            chunk = chunk.replace('\n', '\\n')
            logging.info(f"Sending message to user '{get_name_from_database(destination)}' ({destination}) with sendID {d.id}: \"{chunk}\"")
            time.sleep(5)
        except Exception as e:
            logging.info(f"REPLY SEND ERROR {e.message}")


def send_bulletin_to_bbs_nodes(board, sender_short_name, subject, content, unique_id, bbs_nodes, interface):
    message = f"BULLETIN|{board}|{sender_short_name}|{subject}|{content}|{unique_id}"
    for node_id in bbs_nodes:
        send_message(message, node_id, interface)


def send_mail_to_bbs_nodes(sender_id, sender_short_name, recipient_id, subject, content, unique_id, bbs_nodes,
                           interface):
    message = f"MAIL|{sender_id}|{sender_short_name}|{recipient_id}|{subject}|{content}|{unique_id}"
    logging.info(f"SERVER SYNC: Syncing new mail message {subject} sent from {sender_short_name} to other BBS systems.")
    for node_id in bbs_nodes:
        send_message(message, node_id, interface)


def send_delete_bulletin_to_bbs_nodes(bulletin_id, bbs_nodes, interface):
    message = f"DELETE_BULLETIN|{bulletin_id}"
    for node_id in bbs_nodes:
        send_message(message, node_id, interface)


def send_delete_mail_to_bbs_nodes(unique_id, bbs_nodes, interface):
    message = f"DELETE_MAIL|{unique_id}"
    logging.info(f"SERVER SYNC: Sending delete mail sync message with unique_id: {unique_id}")
    for node_id in bbs_nodes:
        send_message(message, node_id, interface)


def send_channel_to_bbs_nodes(name, url, bbs_nodes, interface):
    message = f"CHANNEL|{name}|{url}"
    for node_id in bbs_nodes:
        send_message(message, node_id, interface)

def split_into_chunks(
    s: str,
    max_bytes: int = 200,
    split_chars: list = None
) -> list:
    """
    Splits a string into chunks of up to max_bytes, trying to split at contextually
    appropriate points (spaces, punctuation). Maintains valid UTF-8 encoding.
    """
    if split_chars is None:
        split_chars = [' ', '\n', '.', ',', '!', '?', ';', ':', '\t', '(', ')', '[', ']', '{', '}']

    split_bytes = [ord(c) for c in split_chars if len(c.encode('utf-8')) == 1]
    encoded = s.encode('utf-8')
    chunks = []
    start = 0
    total_bytes = len(encoded)

    if total_bytes < 128:
        chunks.append(encoded.decode('utf-8'))
        return chunks

    while start < total_bytes:
        end = min(start + max_bytes, total_bytes)
        
        # Ensure we don't check beyond the byte array
        safe_end = min(end, total_bytes - 1)
        
        # Backtrack to avoid splitting multi-byte characters
        while safe_end > start and (encoded[safe_end] & 0b11000000) == 0b10000000:
            safe_end -= 1

        # Find last valid split character
        split_pos = -1
        for i in range(min(safe_end, total_bytes-1), start-1, -1):
            if encoded[i] in split_bytes:
                split_pos = i
                break

        # Determine actual chunk end
        if split_pos != -1:
            actual_end = split_pos + 1
        else:
            actual_end = safe_end

        # Final validation to prevent empty/infinite loops
        if actual_end <= start:
            actual_end = min(start + max_bytes, total_bytes)
            while actual_end > start and actual_end < total_bytes and (encoded[actual_end] & 0b11000000) == 0b10000000:
                actual_end -= 1
            actual_end = max(actual_end, start + 1)

        chunks.append(encoded[start:actual_end].decode('utf-8'))
        start = actual_end

    return chunks

def get_functions(obj):
    return [item[0] for item in inspect.getmembers(obj) if inspect.isfunction(item[1])]

def get_function(obj, function_name, context, choice, packet):
    return getattr(obj, function_name)(context, choice, packet)
