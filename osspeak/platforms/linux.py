'''
Collection of linux-specific I/O functions
'''

import subprocess
import sys
import termios
from platforms import linuxconstants

def flush_io_buffer():
    termios.tcflush(sys.stdin, termios.TCIFLUSH)

def type_literal(keys, delay=0):
    transcribe_line([keys], delay)

def type_keypresses(keys, direction='both'):
    press_key_combination(keys, 0)

def transcribe_line(key_inputs, delay=0, direction=''):
    delay = delay/1000 # seconds to milliseconds
    for key_input in key_inputs:
        if isinstance(key_input, str):
            subprocess.call(['xdotool', 'type', '--delay', f'{delay}ms', key_input])
        else:
            press_key_combination(key_input.keys, delay)

def press_key_combination(keys, delay):
    xdotool_keys = [linuxconstants.XDOTOOL_KEYMAP.get(k.lower(), k) for k in keys] 
    subprocess.call(['xdotool', 'key', '--delay', f'{delay}ms', '+'.join(xdotool_keys)])

def get_mouse_location():
    return subprocess.check_output(['xdotool', 'getmouselocation'])

def mouse_click(button, direction, number):
    button_map = {
        'left': '1',
        'middle': '2',
        'right': '3',
        'wheel up': '4',
        'wheel down': '5',
    }
    button = button_map[button]
    if direction == 'both': command = 'click'
    elif direction == 'down': command = 'mousedown'
    elif direction == 'up': command = 'mouseup'
    else: return
    subprocess.call(['xdotool', command, '--repeat', str(number), button])

def mouse_move(x, y, relative):
    if not relative:
        startx, starty = get_mouse_location()
        if x is None: x = startx
        if y is None: y = starty
        subprocess.call(['xdotool', 'mousemove', str(x), str(y)])
        return
    if x is None: x = 0
    if y is None: y = 0
    subprocess.call(['xdotool', 'mousemove_relative', '--', str(x), str(y)])

def get_active_window_name():
    proc = subprocess.check_output(['xdotool', 'getactivewindow', 'getwindowname'])
    return proc.decode('utf8').rstrip('\n')

def get_open_window_names():
    '''
    Return a dict with open program names and their corresponding decimal ids
    '''
    raw_names = subprocess.check_output(['wmctrl', '-l']).decode('utf8').split('\n')
    split_names = [name.split() for name in raw_names if name]
    name_dict = {}
    for name in split_names:
        if not int(name[1]):
            name_dict[' '.join(name[3:]).lower()] = name[0]
    return name_dict

def activate_window(title):
    name_dict = get_open_window_names()
    matches = []
    for open_window_name in name_dict:
        for name in title:
            if name not in open_window_name:
                break
        else:
            matches.append(open_window_name)
    if matches:
        shortest_matching_name = min(matches, key=len)
        pid = str(int(name_dict[shortest_matching_name], 16))
        subprocess.call(['xdotool', 'windowfocus', pid])
        subprocess.call(['xdotool', 'windowactivate', pid])

def get_clipboard_contents():
    try:
        return subprocess.check_output(['xclip', '-selection', 'c', '-o']).decode('utf8')
    # empty clipboard
    except subprocess.CalledProcessError:
        return ''

def set_clipboard_contents(text):
    p = subprocess.Popen(['xclip', '-selection', 'c'], stdin=subprocess.PIPE)
    p.communicate(input=bytes(text, 'utf-8'))

def close_active_window():
    # subprocess.check_output(['xkill', '-id', 'xprop', '-root', '_NET_ACTIVE_WINDOW', '|', 'cut', '-d\#', '-f2'])
    proc = subprocess.check_output(['xdotool', 'getactivewindow', 'windowkill'])

def maximize_active_window():
    subprocess.check_output(['xdotool', 'windowsize', '$(xdotool getactivewindow)', '100%', '100%'])