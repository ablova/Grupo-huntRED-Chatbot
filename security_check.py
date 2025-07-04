#!/usr/bin/env python3
"""
Security check script for AI HuntRED
Scans the codebase for common security vulnerabilities
"""

import os
import re
import sys
from pathlib import Path


class SecurityChecker:
    def __init__(self):
        self.issues = []
        self.warnings = []
        
    def add_issue(self, severity, file_path, line_num, issue):
        self.issues.append({
            'severity': severity,
            'file': file_path,
            'line': line_num,
            'issue': issue
        })
    
    def add_warning(self, message):
        self.warnings.append(message)
    
    def check_hardcoded_secrets(self, content, file_path):
        """Check for hardcoded secrets in code"""
        patterns = [
            (r'(?i)(api[_-]?key|apikey)\s*=\s*["\'][\w\-]{20,}["\']', 'Hardcoded API key'),
            (r'(?i)(secret[_-]?key|secretkey)\s*=\s*["\'][\w\-]{20,}["\']', 'Hardcoded secret key'),
            (r'(?i)password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password'),
            (r'(?i)token\s*=\s*["\'][\w\-]{20,}["\']', 'Hardcoded token'),
            (r'(?i)private[_-]?key\s*=\s*["\'][^"\']+["\']', 'Hardcoded private key'),
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, issue_type in patterns:
                if re.search(pattern, line):
                    # Skip if it's a variable assignment from env
                    if 'os.environ' in line or 'os.getenv' in line:
                        continue
                    # Skip if it's an example or placeholder
                    if any(x in line.lower() for x in ['example', 'your-', 'xxx', 'placeholder']):
                        continue
                    self.add_issue('CRITICAL', file_path, i, issue_type)
    
    def check_sql_injection(self, content, file_path):
        """Check for potential SQL injection vulnerabilities"""
        patterns = [
            (r'\.raw\s*\([^)]*%[^)]*\)', 'SQL injection risk: raw query with string formatting'),
            (r'\.raw\s*\([^)]*\.format\s*\(', 'SQL injection risk: raw query with .format()'),
            (r'\.raw\s*\([^)]*\+[^)]*\)', 'SQL injection risk: raw query with string concatenation'),
            (r'cursor\.execute\s*\([^)]*%[^)]*\)', 'SQL injection risk: execute with % formatting'),
            (r'cursor\.execute\s*\([^)]*\.format', 'SQL injection risk: execute with .format()'),
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, issue_type in patterns:
                if re.search(pattern, line):
                    self.add_issue('HIGH', file_path, i, issue_type)
    
    def check_csrf_exempt(self, content, file_path):
        """Check for CSRF exemptions"""
        if '@csrf_exempt' in content:
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if '@csrf_exempt' in line:
                    self.add_issue('HIGH', file_path, i, 'CSRF protection disabled')
    
    def check_xss_vulnerabilities(self, content, file_path):
        """Check for XSS vulnerabilities in templates"""
        if file_path.endswith('.html'):
            patterns = [
                (r'\{\{[^}]*\|safe\}\}', 'XSS risk: using |safe filter'),
                (r'\{\%\s*autoescape\s+off\s*\%\}', 'XSS risk: autoescape disabled'),
                (r'mark_safe\s*\(', 'XSS risk: using mark_safe'),
            ]
            
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                for pattern, issue_type in patterns:
                    if re.search(pattern, line):
                        self.add_issue('HIGH', file_path, i, issue_type)
    
    def check_debug_mode(self, content, file_path):
        """Check for debug mode in production"""
        if 'settings.py' in file_path or 'config.py' in file_path:
            if re.search(r'DEBUG\s*=\s*True', content):
                self.add_issue('MEDIUM', file_path, 0, 'DEBUG mode enabled')
    
    def check_file(self, file_path):
        """Check a single file for security issues"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            self.check_hardcoded_secrets(content, file_path)
            self.check_sql_injection(content, file_path)
            self.check_csrf_exempt(content, file_path)
            self.check_xss_vulnerabilities(content, file_path)
            self.check_debug_mode(content, file_path)
            
        except Exception as e:
            self.add_warning(f"Could not check {file_path}: {str(e)}")
    
    def scan_directory(self, directory):
        """Scan all Python and template files in directory"""
        extensions = ['.py', '.html', '.js']
        exclude_dirs = ['venv', 'node_modules', '.git', '__pycache__', 'migrations']
        
        for root, dirs, files in os.walk(directory):
            # Remove excluded directories from search
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    self.check_file(file_path)
    
    def generate_report(self):
        """Generate security report"""
        print("=" * 80)
        print("SECURITY SCAN REPORT")
        print("=" * 80)
        
        if not self.issues:
            print("\n✅ No security issues found!")
        else:
            # Group by severity
            critical = [i for i in self.issues if i['severity'] == 'CRITICAL']
            high = [i for i in self.issues if i['severity'] == 'HIGH']
            medium = [i for i in self.issues if i['severity'] == 'MEDIUM']
            low = [i for i in self.issues if i['severity'] == 'LOW']
            
            print(f"\nTotal issues found: {len(self.issues)}")
            print(f"  - CRITICAL: {len(critical)}")
            print(f"  - HIGH: {len(high)}")
            print(f"  - MEDIUM: {len(medium)}")
            print(f"  - LOW: {len(low)}")
            
            # Print issues by severity
            for severity, issues in [('CRITICAL', critical), ('HIGH', high), 
                                   ('MEDIUM', medium), ('LOW', low)]:
                if issues:
                    print(f"\n{severity} SEVERITY ISSUES:")
                    print("-" * 40)
                    for issue in issues[:10]:  # Show first 10 of each type
                        print(f"File: {issue['file']}")
                        print(f"Line: {issue['line']}")
                        print(f"Issue: {issue['issue']}")
                        print()
                    
                    if len(issues) > 10:
                        print(f"... and {len(issues) - 10} more {severity} issues")
        
        if self.warnings:
            print("\nWARNINGS:")
            print("-" * 40)
            for warning in self.warnings[:5]:
                print(f"- {warning}")
            if len(self.warnings) > 5:
                print(f"... and {len(self.warnings) - 5} more warnings")
        
        print("\n" + "=" * 80)
        
        # Return exit code based on critical issues
        return 1 if any(i['severity'] == 'CRITICAL' for i in self.issues) else 0


def main():
    checker = SecurityChecker()
    
    # Scan the current directory or specified path
    scan_path = sys.argv[1] if len(sys.argv) > 1 else '.'
    
    print(f"Scanning {scan_path} for security issues...")
    checker.scan_directory(scan_path)
    
    exit_code = checker.generate_report()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()