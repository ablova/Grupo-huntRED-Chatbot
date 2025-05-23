#!/usr/bin/env python3
"""
Script to fix send_email usages in amigro.py.
This script replaces direct calls to send_email with proper EmailService instantiation and usage.
"""
import re

# Target file
file_path = '/Users/pablollh/MEGA/GitHub/Grupo-huntRED-Chatbot/app/com/chatbot/workflow/business_units/amigro/amigro.py'

# Read file content
with open(file_path, 'r') as f:
    content = f.read()

# Regular expression patterns
# This matches standalone send_email function calls with named parameters
pattern1 = r'send_email\((?P<params>[^)]+)\)'

# Function to process each match
def process_match(match):
    params = match.group('params')
    
    # Convert parameters to a dictionary
    param_dict = {}
    for param in params.split(','):
        if '=' in param:
            key, value = param.split('=', 1)
            param_dict[key.strip()] = value.strip()
    
    # Check if 'to' parameter exists
    if 'to' not in param_dict and 'business_unit' not in param_dict:
        # If no business unit parameter, we'll need to use a default
        return f"# Initialize EmailService with appropriate business unit\nemail_service = EmailService(BusinessUnit.objects.get(name='Amigro'))\nawait email_service.send_email({params})"
    elif 'business_unit' in param_dict:
        # If business_unit parameter exists
        bu_param = param_dict['business_unit']
        del param_dict['business_unit']
        other_params = ', '.join([f'{k}={v}' for k, v in param_dict.items()])
        return f"email_service = EmailService({bu_param})\nawait email_service.send_email({other_params})"
    else:
        # Standard case with all parameters
        return f"# Initialize EmailService with appropriate business unit\nemail_service = EmailService(BusinessUnit.objects.get(name='Amigro'))\nawait email_service.send_email({params})"

# Apply the replacements
modified_content = re.sub(pattern1, lambda m: process_match(m), content)

# Write the modified content back to the file
with open(file_path, 'w') as f:
    f.write(modified_content)

print(f"Updated {file_path} with EmailService usages.")
