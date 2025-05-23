#!/usr/bin/env python
import re

file_path = '/Users/pablollh/MEGA/GitHub/Grupo-huntRED-Chatbot/app/com/chatbot/workflow/common/common.py'

with open(file_path, 'r') as f:
    content = f.read()

# Replace all instances of "await send_options(" with "await send_options_async("
modified_content = re.sub(r'await send_options\(', 'await send_options_async(', content)

with open(file_path, 'w') as f:
    f.write(modified_content)

print("Replacements completed.")
