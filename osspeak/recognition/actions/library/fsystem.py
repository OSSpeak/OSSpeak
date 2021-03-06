import os
from settings import settings

def read_file(path):
    if isinstance(path, (list, tuple)):
        path = os.path.join(path)
    cwd = os.getcwd()
    os.chdir(settings['command_directory'])
    try:
        with open(path) as f:
            text = f.read()
    finally:
        os.chdir(cwd)
    return text
    
def write_file(path, text):
    if isinstance(path, (list, tuple)):
        path = os.path.join(path)
    cwd = os.getcwd()
    os.chdir(settings['command_directory'])
    with open(path, 'w') as f:
        f.write(text)
    os.chdir(cwd)
