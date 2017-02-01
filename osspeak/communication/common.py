import json
import time
from communication import messages

TERMINATION_SEQUENCE = 'f1a5238b-ec60-430e-a0a8-5fe7442273a0'

def receive_loop(sock):
    leftover = ''
    while True:
        msg = sock.recv(65536).strip()
        if msg:
            leftover = receive_message(leftover, msg)

def receive_message(prefix, message_bytes):
    message_text = message_bytes.decode('utf-8')
    message_list = message_text.split(TERMINATION_SEQUENCE)
    message_list[0] = f'{prefix}{message_list[0]}'
    leftover_text = message_list.pop()
    for msg in message_list:
        message_object = json.loads(msg)
        messages.dispatch(message_object['name'], *message_object['args'], **message_object['kwargs'])
    return leftover_text

def send_message(socket, msg_name, *args, **kwargs):
    msg = {
        'name': msg_name,
        'args': args,
        'kwargs': kwargs,
    }
    encoded_message = json.dumps(msg)
    msg_bytes = bytes(f'{encoded_message}{TERMINATION_SEQUENCE}', 'utf-8')
    socket.sendall(msg_bytes)
