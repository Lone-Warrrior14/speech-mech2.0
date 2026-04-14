import os
import sys

# Simulate the same path resolution as web_server.py
base_dir = r"d:\SPEECH_MECH3\SPEECH_MECH\launch_web_system"
root_dir = os.path.dirname(base_dir)

# Path to media_library's folder
media_lib_dir = os.path.join(root_dir, 'speech_assistant', 'media')
sys.path.append(media_lib_dir)

import media_library

print(f"ROOT_DIR: {root_dir}")
print(f"MEDIA_LIB_DIR: {media_lib_dir}")
print(f"MEDIA_FOLDER in media_library: {media_library.MEDIA_FOLDER}")
print(f"Exists? {os.path.exists(media_library.MEDIA_FOLDER)}")
print(f"Movies: {media_library.get_movies()}")
