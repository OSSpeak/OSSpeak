from log import logger
import queue
import threading
import collections

EMULATE_RECOGNITION = 'emulate recognition'
ENGINE_START = 'engine start'
ENGINE_STOP = 'engine stop'
HEARTBEAT = 'heartbeat'
LOAD_MODULE_MAP = 'load module map'
PERFORM_COMMANDS = 'perform commands'
RELOAD_COMMAND_MODULE_FILES = 'reload command module files'
SET_SAVED_MODULES = 'set saved modules'
LOAD_GRAMMAR = 'load grammar'
RELOAD_GRAMMAR = 'reload grammar'
STOP_MAIN_PROCESS  = 'shutdown'
ENGINE_CONNECTION_OK = 'ENGINE_CONNECTION_OK'
ENGINE_CONNECTION_BROKEN = 'ENGINE_CONNECTION_BROKEN'
WEBSOCKET_CONNECTION_ESTABLISHED = 'websocket connection established'
WEBSOCKET_CONNECTION_BROKEN = 'websocket connection broken'
RECEIVED_WEBSOCKET_MESSAGE = 'RECEIVED_WEBSOCKET_MESSAGE'
POLL_ENGINE_SERVER = 'POLL_ENGINE_SERVER'
SET_ENGINE_STATUS = 'SET_ENGINE_STATUS'
MESSAGE_GUI = 'MESSAGE_GUI'

_subscriptions = collections.defaultdict(list)
_subscription_lock = threading.Lock()

def dispatch(message_name, *args, **kwargs):
    logger.debug(f"Dispatching message: '{message_name}'")
    with _subscription_lock:
        for sub in _subscriptions[message_name]:
            sub.payload_queue.put((args, kwargs))

def dispatch_sync(message_name, *args, **kwargs):
    logger.debug(f"Dispatching sync message: '{message_name}'")
    with _subscription_lock:
        subscriptions = _subscriptions[message_name].copy()
    for sub in subscriptions:
        sub.callback(*args, **kwargs)

def subscribe(message_name, callback):
    if not callable(callback):
        raise TypeError(f'Callback for message {message_name} must be callable')
    sub = Subscription(callback, message_name)
    _subscriptions[message_name].append(sub)
    return sub

def unsubscribe(subscription):
    with _subscription_lock:
        if subscription.name in _subscriptions:
            _subscriptions[subscription.name] = [s for s in _subscriptions[subscription.name] if s is not subscription]
            if not _subscriptions[subscription.name]:
                del _subscriptions[subscription.name]
        subscription.stop()

class Subscription:

    def __init__(self, callback, name):
        self.callback = callback
        self.name = name
        self.payload_queue = queue.Queue()
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        while True:
            payload = self.payload_queue.get()
            if payload is None:
                return
            self.callback(*payload[0], **payload[1])

    def stop(self):
        self.payload_queue.put(None)
