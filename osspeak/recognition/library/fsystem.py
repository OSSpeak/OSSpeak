import os
from user.settings import user_settings

def read_file(path):
    cwd = os.getcwd()
    os.chdir(user_settings['command_directory'])
    with open(path) as f:
        text = f.read()
    os.chdir(cwd)
    return text
    
def write_file(path, text):
    cwd = os.getcwd()
    os.chdir(user_settings['command_directory'])
    with open(path, 'w') as f:
        f.write(text)
    os.chdir(cwd)