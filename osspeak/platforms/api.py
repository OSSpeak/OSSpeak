import sys

def load_platform_module():
	if sys.platform == 'win32':
		from platforms import windows
		return windows
	elif sys.platform == 'linux':
		from platforms import linux
		return linux
	raise RuntimeError(f'Unsupported platform: {sys.platform}')

platform = load_platform_module()

def flush_io_buffer():
	platform.flush_io_buffer()

def get_active_window_name():
	return platform.get_active_window_name()
	
def maximize_active_window():
	platform.maximize_active_window()

def transcribe_line(key_inputs, delay, direction):
    platform.transcribe_line(key_inputs, delay, direction)

def get_mouse_location():
	return platform.get_mouse_location()

def mouse_click(button='left', direction='both', number=1):
	platform.mouse_click(button, direction, number)

def mouse_move(x, y, relative):
	platform.mouse_move(x, y, relative)

def activate_window(title):
    if isinstance(title, str):
        title = [title]
    title = [name.lower() for name in title]
    platform.activate_window(title)

def get_clipboard_contents():
    return platform.get_clipboard_contents()

def set_clipboard_contents(text):
    platform.set_clipboard_contents(text)

def type_line(evaluated_item_list):
	for item in evaluated_item_list:
		if isinstance(item, str):
			type_literal(item)
		elif isinstance(item, list):
			for key_combination in item:
				key_combination = [key_combination] if isinstance(key_combination, str) else key_combination
				type_keypresses(key_combination)
		else:
			raise TypeError

def type_literal(text):
	platform.type_literal(text)

def type_keypresses(text, direction='both'):
	platform.type_keypresses(text, direction=direction)

def close_active_window():
	platform.close_active_window()