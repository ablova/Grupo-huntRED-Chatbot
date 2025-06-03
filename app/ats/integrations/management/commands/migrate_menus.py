"""
Migration script for the new menu system.

This script migrates from the old menu system to the new dynamic menu system.
"""

from django.core.management.base import BaseCommand
from django.apps import apps
import os
import shutil

class Command(BaseCommand):
    help = 'Migrate from old menu system to new dynamic menu system'

    def handle(self, *args, **options):
        self.stdout.write("Starting menu system migration...")
        
        # 1. Replace the menu.py file
        self.migrate_menu_file()
        
        # 2. Clean up old cultural assessment implementation
        self.cleanup_old_implementation()
        
        self.stdout.write(self.style.SUCCESS('Successfully migrated to new menu system'))
    
    def migrate_menu_file(self):
        """Replace the old menu.py with the new implementation"""
        try:
            # Get the base directory
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            
            # Paths relative to the base directory
            old_menu_path = os.path.join(base_dir, 'ats', 'integrations', 'services', 'menu.py')
            new_menu_path = os.path.join(base_dir, 'ats', 'integrations', 'services', 'menu_new.py')
            
            # Backup old menu if it exists
            if os.path.exists(old_menu_path):
                backup_path = f"{old_menu_path}.bak"
                shutil.copy2(old_menu_path, backup_path)
                self.stdout.write(f"Backed up old menu to {backup_path}")
            
            # Replace with new menu
            if os.path.exists(new_menu_path):
                shutil.move(new_menu_path, old_menu_path)
                self.stdout.write("Successfully updated menu.py with new implementation")
            else:
                self.stderr.write("Error: New menu file not found")
                
        except Exception as e:
            self.stderr.write(f"Error migrating menu file: {str(e)}")
    
    def cleanup_old_implementation(self):
        """Clean up old cultural assessment implementation"""
        try:
            # Get the base directory
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            cultural_assessment_dir = os.path.join(base_dir, 'cultural_assessment')
            
            if os.path.exists(cultural_assessment_dir):
                # Create backup just in case
                backup_dir = f"{cultural_assessment_dir}_backup"
                if not os.path.exists(backup_dir):
                    shutil.copytree(cultural_assessment_dir, backup_dir)
                    self.stdout.write(f"Created backup of old cultural assessment at {backup_dir}")
                
                # Remove the directory
                shutil.rmtree(cultural_assessment_dir)
                self.stdout.write(f"Removed old cultural assessment directory at {cultural_assessment_dir}")
                
        except Exception as e:
            self.stderr.write(f"Error cleaning up old implementation: {str(e)}")
            self.stderr.write("You may need to manually clean up the old cultural_assessment directory")
    
    def update_imports(self):
        """Update any imports that pointed to the old implementation"""
        # This is a placeholder for any import updates needed
        # In a real scenario, you would want to:
        # 1. Find all Python files that might import from the old module
        # 2. Update the imports to point to the new location
        
        self.stdout.write("Note: Please review and update any remaining imports manually")
