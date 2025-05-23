#!/usr/bin/env python3
"""
Script to fix import statements in all business unit modules.
This script specifically targets the workflow.common imports to ensure they point
to the correct module: app.com.chatbot.workflow.common.common
"""
import os
import re

# Define the base directory
base_dir = '/Users/pablollh/MEGA/GitHub/Grupo-huntRED-Chatbot/app/com/chatbot/workflow/business_units'

# Define patterns to replace
replacements = [
    (r'from app\.com\.chatbot\.workflow\.common import \(([^)]+)\)', 
     r'from app.com.chatbot.workflow.common.common import (\1)'),
    (r'from app\.com\.chatbot\.workflow\.common import ([^(]+)', 
     r'from app.com.chatbot.workflow.common.common import \1'),
]

fixed_files = []
error_files = []

# Walk through all subdirectories
for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.endswith('.py'):
            file_path = os.path.join(root, file)
            print(f"Processing {file_path}")
            
            try:
                # Read file content
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Apply replacements
                original_content = content
                for pattern, replacement in replacements:
                    content = re.sub(pattern, replacement, content)
                
                # Write back if changed
                if content != original_content:
                    with open(file_path, 'w') as f:
                        f.write(content)
                    fixed_files.append(file_path)
                    print(f"  Fixed imports in {file_path}")
                else:
                    print(f"  No changes needed in {file_path}")
            
            except Exception as e:
                print(f"  Error processing {file_path}: {str(e)}")
                error_files.append((file_path, str(e)))

print("\nSummary:")
print(f"Processed {len(fixed_files) + len(error_files)} files")
print(f"Fixed {len(fixed_files)} files")
print(f"Errors in {len(error_files)} files")

if error_files:
    print("\nErrors:")
    for file, error in error_files:
        print(f"  {file}: {error}")

print("\nFixed files:")
for file in fixed_files:
    print(f"  {file}")
