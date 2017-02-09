import os

from platforms import api

def focus(title):
    api.activate_window(title)

def close():
    api.close_active_window()

def maximise_active():
    api.maximize_active_window()

def start(name):
    os.startfile(name)

def shell(text):
    return os.system(text)