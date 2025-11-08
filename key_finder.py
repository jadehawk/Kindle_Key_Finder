#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Kindle Key Finder - Python Edition Wrapper
Replicates the exact DeDRM plugin logic for key extraction and JSON generation
No external dependencies - uses the same methods as the plugin
"""

# Script Version
SCRIPT_VERSION = "2025.11.08.JH"

# Unified Configuration File
CONFIG_FILE = "key_finder_config.json"

import os
import sys
import json
import subprocess
import shutil
import time
import threading
import msvcrt
import platform
from datetime import datetime

def print_colored(message, color):
    """Print colored messages"""
    colors = {
        'cyan': '\033[96m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'red': '\033[91m',
        'magenta': '\033[95m',
        'end': '\033[0m'
    }
    print(f"{colors.get(color, '')}{message}{colors['end']}")

def print_step(message):
    print_colored(f"[*] {message}", 'cyan')

def print_ok(message):
    print_colored(f"[OK] {message}", 'green')

def print_warn(message):
    print_colored(f"[!] {message}", 'yellow')

def print_error(message):
    print_colored(f"[ERROR] {message}", 'red')

def print_done(message):
    print_colored(f"[DONE] {message}", 'magenta')

def print_banner_and_version():
    """Print ASCII banner and script version"""
    print_colored(r" _____         _                   _   _       _                  ____                ", 'green')
    print_colored(r"|_   _|__  ___| |__  _   _        | \ | | ___ | |_ ___  ___      / ___|___  _ __ ___  ", 'green')
    print_colored(r"  | |/ _ \/ __| '_ \| | | | _____ |  \| |/ _ \| __/ _ \/ __|    | |   / _ \| '_ ` _ \ ", 'green')
    print_colored(r"  | |  __/ (__| | | | |_| ||_____|| |\  | (_) | ||  __/\__ \  _ | |__| (_) | | | | | |", 'green')
    print_colored(r"  |_|\___|\___|_| |_|\__, |       |_| \_|\___/ \__\___||___/ (_) \____\___/|_| |_| |_|", 'green')
    print_colored(r"                     |___/                                                             ", 'green')
    print()
    print_step("Kindle Key Finder - Python Edition Wrapper")
    print(f"Script Version: {SCRIPT_VERSION}")
    print()

def display_phase_banner(phase_num, phase_name):
    """
    Display a prominent phase banner with decorative borders
    """
    print()
    print_colored("═" * 70, 'cyan')
    print_colored(f"║{f'PHASE {phase_num}':^68}║", 'cyan')
    print_colored(f"║{phase_name.upper():^68}║", 'cyan')
    print_colored("═" * 70, 'cyan')
    print()

# ============================================================================
# PHASE SUMMARY FUNCTION
# ============================================================================

def display_phase_summary(phase_num, phase_name, summary_points, pause_seconds=5):
    """
    Display phase completion summary with countdown
    Allows user to press any key to skip countdown
    Respects skip_phase_pauses configuration flag
    """
    print()
    print("=" * 70)
    print_done(f"[PHASE {phase_num}] {phase_name} - COMPLETE")
    print("=" * 70)
    print()
    print_step("Summary of accomplishments:")
    for point in summary_points:
        print(f"  ✓ {point}")
    print()
    
    # Check if pauses should be skipped
    config = load_config()
    skip_pauses = config.get('skip_phase_pauses', False) if config else False
    
    if skip_pauses:
        # Skip countdown - just display summary and continue
        print_step("Continuing to next phase...")
        print()
        return
    
    # Show countdown with skip capability
    print(f"Continuing to next phase in {pause_seconds} seconds...")
    print("(Press any key to skip countdown)")
    print()
    
    # Countdown with skip capability
    for i in range(pause_seconds, 0, -1):
        if msvcrt.kbhit():
            msvcrt.getch()  # Consume the keypress
            print("\r" + " " * 50 + "\r", end='', flush=True)
            print_step("Countdown skipped by user")
            print()
            return
        print(f"\r  {i}...", end='', flush=True)
        time.sleep(1)
    
    print("\r" + " " * 20 + "\r", end='', flush=True)
    print()

def obfuscate_sensitive(text):
    """
    Obfuscate sensitive strings by showing first 2 and last 2 characters
    Example: 'Pd545vnnr861r5P0Pt6ttP7nP6tA6b57Pt7fS1rh' -> 'Pd**********************rh'
    """
    if len(text) <= 4:
        return text  # Too short to obfuscate meaningfully
    return text[:2] + '*' * (len(text) - 4) + text[-2:]

def filter_sensitive_output(text, hide_sensitive=False):
    """
    Filter and obfuscate sensitive information in output text if hide_sensitive is enabled
    Also always suppresses harmless Qt and Fontconfig error messages
    """
    import re
    lines = text.split('\n')
    filtered_lines = []
    
    for line in lines:
        # Always skip Qt and Fontconfig error messages (regardless of hide_sensitive)
        if 'QObject::startTimer: Timers can only be used with threads started with QThread' in line:
            continue
        if 'Fontconfig error: Cannot load default config file' in line:
            continue
        
        # If obfuscation is disabled, keep the line as-is
        if not hide_sensitive:
            filtered_lines.append(line)
            continue
        
        filtered_line = line
        
        # Obfuscate DSN values
        if line.startswith('DSN '):
            dsn_value = line.replace('DSN ', '').strip()
            if dsn_value:
                filtered_line = f"DSN {obfuscate_sensitive(dsn_value)}"
        
        # Obfuscate Tokens
        elif line.startswith('Tokens '):
            tokens_value = line.replace('Tokens ', '').strip()
            if tokens_value:
                # Handle comma-separated tokens
                if ',' in tokens_value:
                    token_parts = tokens_value.split(',')
                    obfuscated_parts = [obfuscate_sensitive(part.strip()) for part in token_parts]
                    filtered_line = f"Tokens {','.join(obfuscated_parts)}"
                else:
                    filtered_line = f"Tokens {obfuscate_sensitive(tokens_value)}"
        
        # Obfuscate DRM key with UUID and secret key
        elif 'amzn1.drm-key.v1.' in line and '$secret_key:' in line:
            # Pattern: amzn1.drm-key.v1.UUID$secret_key:SECRET
            match = re.search(r'(amzn1\.drm-key\.v1\.)([a-f0-9\-]+)(\$secret_key:)([a-f0-9]+)', line)
            if match:
                prefix = match.group(1)  # amzn1.drm-key.v1.
                uuid = match.group(2)     # UUID
                middle = match.group(3)   # $secret_key:
                secret = match.group(4)   # secret value
                
                obfuscated_uuid = obfuscate_sensitive(uuid)
                obfuscated_secret = obfuscate_sensitive(secret)
                
                original = f"{prefix}{uuid}{middle}{secret}"
                replacement = f"{prefix}{obfuscated_uuid}{middle}{obfuscated_secret}"
                filtered_line = line.replace(original, replacement)
        
        # Obfuscate secret keys (fallback for lines without UUID)
        elif '$secret_key:' in line:
            parts = line.split('$secret_key:')
            if len(parts) == 2:
                prefix = parts[0]
                secret = parts[1].strip()
                if secret:
                    filtered_line = f"{prefix}$secret_key:{obfuscate_sensitive(secret)}"
        
        # Obfuscate "Opened book with secret:" (handles both hex and base64)
        elif 'Opened book with secret:' in line:
            match = re.search(r'(Opened book with secret:\s*)([A-Za-z0-9+/=]+)', line)
            if match:
                prefix = match.group(1)
                secret = match.group(2)
                obfuscated = obfuscate_sensitive(secret)
                filtered_line = line.replace(f"{prefix}{secret}", f"{prefix}{obfuscated}")
        
        # Obfuscate "Opened book with reused secret:" (handles both hex and base64)
        elif 'Opened book with reused secret:' in line:
            match = re.search(r'(Opened book with reused secret:\s*)([A-Za-z0-9+/=]+)', line)
            if match:
                prefix = match.group(1)
                secret = match.group(2)
                obfuscated = obfuscate_sensitive(secret)
                filtered_line = line.replace(f"{prefix}{secret}", f"{prefix}{obfuscated}")
        
        # Obfuscate "Working secret:" (handles both hex and base64)
        elif 'Working secret:' in line:
            match = re.search(r'(Working secret:\s*")([A-Za-z0-9+/=]+)(")', line)
            if match:
                prefix = match.group(1)
                secret = match.group(2)
                suffix = match.group(3)
                obfuscated = obfuscate_sensitive(secret)
                filtered_line = line.replace(f"{prefix}{secret}{suffix}", f"{prefix}{obfuscated}{suffix}")
        
        # Obfuscate device_serial_number in JSON format
        elif '"device_serial_number":"' in line:
            match = re.search(r'"device_serial_number":"([^"]+)"', line)
            if match:
                serial = match.group(1)
                obfuscated = obfuscate_sensitive(serial)
                filtered_line = line.replace(f'"{serial}"', f'"{obfuscated}"')
        
        filtered_lines.append(filtered_line)
    
    return '\n'.join(filtered_lines)

def get_kindle_content_path(default_path):
    """
    Prompt user to confirm or modify the Kindle content directory path
    Handles Windows-specific path scenarios with 5-second auto-proceed timer
    """
    import threading
    import msvcrt
    
    print_step("Kindle-4-PC Book's Path Configuration")
    print("--------------------------------------------------")
    print(f"Default path: {default_path}")
    print()
    print("Press Enter to accept default immediately, or start typing for custom path")
    print("(Auto-proceeding with default in 5 seconds if no input...)")
    print()
    
    # Shared state for timer and input
    timer_cancelled = threading.Event()
    user_input_started = threading.Event()
    countdown_active = True
    
    def countdown_timer():
        nonlocal countdown_active
        for i in range(5, 0, -1):
            if timer_cancelled.is_set() or user_input_started.is_set():
                countdown_active = False
                return
            print(f"\rCountdown: {i} seconds... ", end='', flush=True)
            time.sleep(1)
        countdown_active = False
        if not user_input_started.is_set():
            print("\r" + " " * 50 + "\r", end='', flush=True)  # Clear countdown line
            print_ok("Auto-proceeding with default path")
            timer_cancelled.set()
    
    # Start countdown timer
    timer_thread = threading.Thread(target=countdown_timer, daemon=True)
    timer_thread.start()
    
    # Wait for user input or timer expiry
    user_input = ""
    input_buffer = []
    
    while countdown_active or user_input_started.is_set():
        if msvcrt.kbhit():
            char = msvcrt.getwche()
            
            if not user_input_started.is_set():
                # First keypress - cancel timer
                user_input_started.set()
                timer_cancelled.set()
                print("\r" + " " * 50 + "\r", end='', flush=True)  # Clear countdown
                
                # Check if it's Enter key
                if char == '\r':
                    print()
                    user_input = ""
                    break
                else:
                    print("> ", end='', flush=True)
                    print(char, end='', flush=True)
                    input_buffer.append(char)
            else:
                # Continue collecting input
                if char == '\r':
                    print()
                    user_input = ''.join(input_buffer)
                    break
                elif char == '\b':  # Backspace
                    if input_buffer:
                        input_buffer.pop()
                        print(' \b', end='', flush=True)
                else:
                    input_buffer.append(char)
        elif not countdown_active and not user_input_started.is_set():
            # Timer expired, no input
            break
        else:
            time.sleep(0.05)
    
    user_input = user_input.strip()
    
    # If user pressed Enter without typing, use default
    if not user_input:
        content_path = default_path
    else:
        # Clean up the input path
        # Remove quotation marks (both single and double)
        content_path = user_input.strip('"').strip("'")
        
        # Expand environment variables like %USERPROFILE%
        content_path = os.path.expandvars(content_path)
        
        # Normalize path separators for Windows (convert / to \)
        content_path = os.path.normpath(content_path)
    
    # Validate path exists
    if os.path.exists(content_path):
        print_ok(f"Using path: {content_path}")
        print()
        return content_path
    else:
        print_error(f"Path does not exist: {content_path}")
        print()
        # Ask again or exit
        retry = input("Would you like to try again? (y/n): ").lower()
        if retry == 'y':
            return get_kindle_content_path(default_path)
        else:
            raise FileNotFoundError(f"Kindle content directory not found: {content_path}")

def cleanup_temp_kindle():
    """
    Check for and cleanup any leftover temporary Kindle installation
    from previous failed runs
    """
    user_home = os.path.expanduser("~")
    temp_kindle_dir = os.path.join(user_home, "AppData", "Local", "Amazon", "Kindle", "application")
    temp_marker = os.path.join(temp_kindle_dir, "TEMP.txt")
    
    if os.path.exists(temp_marker):
        print_warn("Found leftover temporary Kindle installation from previous run")
        print_step("Cleaning up...")
        try:
            shutil.rmtree(temp_kindle_dir)
            print_ok("Cleanup completed successfully")
        except Exception as e:
            print_error(f"Failed to cleanup temporary files: {e}")
            print_warn("You may need to manually delete: " + temp_kindle_dir)
        print()

def cleanup_temp_extraction(silent=False):
    """
    Check for and cleanup any leftover temp_extraction folder
    from previous failed runs
    
    Args:
        silent: If True, don't print messages (for use during extraction)
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    temp_extraction_dir = os.path.join(script_dir, "temp_extraction")
    
    if os.path.exists(temp_extraction_dir):
        if not silent:
            print_warn("Found leftover temp_extraction folder from previous run")
            print_step("Cleaning up...")
        try:
            shutil.rmtree(temp_extraction_dir)
            if not silent:
                print_ok("Cleanup completed successfully")
        except Exception as e:
            if not silent:
                print_error(f"Failed to cleanup temp_extraction folder: {e}")
                print_warn("You may need to manually delete: " + temp_extraction_dir)
        if not silent:
            print()

def find_kindle_exe():
    """
    Search for Kindle.exe in the two known installation locations
    Returns tuple: (kindle_dir, is_temp_copy_needed)
    """
    user_home = os.path.expanduser("~")
    
    # Location 1: AppData (default installation)
    appdata_kindle = os.path.join(user_home, "AppData", "Local", "Amazon", "Kindle", "application")
    appdata_exe = os.path.join(appdata_kindle, "Kindle.exe")
    temp_marker = os.path.join(appdata_kindle, "TEMP.txt")
    
    # Location 2: Program Files (x86)
    program_files_kindle = r"C:\Program Files (x86)\Amazon\Kindle"
    program_files_exe = os.path.join(program_files_kindle, "Kindle.exe")
    
    print_step("Searching for Kindle installation...")
    print("--------------------------------------------------")
    
    # Check both locations
    appdata_exists = os.path.exists(appdata_exe)
    program_files_exists = os.path.exists(program_files_exe)
    
    # CASE 1: Both locations have Kindle.exe
    if appdata_exists and program_files_exists:
        print_warn("Found Kindle.exe in BOTH locations:")
        print(f"  1. {appdata_kindle}")
        print(f"  2. {program_files_kindle}")
        print()
        print_error("CONFLICT DETECTED!")
        print("This suggests Kindle is installed in Global mode (Program Files)")
        print("but there's also a copy in AppData (possibly leftover or temp copy).")
        print()
        print_warn("Recommended action: Delete AppData copy and use Program Files installation")
        print()
        print("Options:")
        print("  [C] Continue - Delete AppData copy and proceed with Program Files installation")
        print("  [Q] Quit - Exit script and resolve manually")
        print()
        
        while True:
            choice = input("Your choice (C/Q): ").strip().upper()
            if choice == 'C':
                print()
                print_step("Deleting AppData Kindle copy...")
                try:
                    shutil.rmtree(appdata_kindle)
                    print_ok("AppData copy deleted successfully")
                    print()
                    # Now proceed with Program Files installation
                    print_ok(f"Using Kindle at: {program_files_kindle}")
                    print_warn("KFXKeyExtractor requires Kindle in AppData location")
                    print()
                    print_step("Solution: Temporary copy will be created")
                    print("  - Source: " + program_files_kindle)
                    print("  - Destination: " + appdata_kindle)
                    print("  - This copy will be automatically deleted after extraction")
                    print("--------------------------------------------------")
                    print()
                    return program_files_kindle, True
                except Exception as e:
                    print_error(f"Failed to delete AppData copy: {e}")
                    print_error("Please manually delete the folder and try again")
                    print("--------------------------------------------------")
                    print()
                    return None, False
            elif choice == 'Q':
                print()
                print_warn("Script cancelled by user")
                print("Please manually resolve the dual installation before running again")
                print("--------------------------------------------------")
                print()
                return None, False
            else:
                print_error("Invalid choice. Please enter C or Q.")
    
    # CASE 2: Only AppData location has Kindle.exe
    elif appdata_exists:
        # Make sure it's not a temp copy (shouldn't have TEMP.txt if real installation)
        if not os.path.exists(temp_marker):
            print_ok(f"Found Kindle at: {appdata_kindle}")
            print_ok("Using existing installation (no temporary copy needed)")
            print("--------------------------------------------------")
            print()
            return appdata_kindle, False
        else:
            # Has TEMP.txt marker - this is a leftover temp copy
            print_warn(f"Found Kindle at: {appdata_kindle}")
            print_warn("But TEMP.txt marker detected - this appears to be a leftover temp copy")
            print_step("Cleaning up leftover temp copy...")
            try:
                shutil.rmtree(appdata_kindle)
                print_ok("Cleanup completed")
                print()
                # Check Program Files again
                if os.path.exists(program_files_exe):
                    print_ok(f"Found Kindle at: {program_files_kindle}")
                    print_warn("KFXKeyExtractor requires Kindle in AppData location")
                    print()
                    print_step("Solution: Temporary copy will be created")
                    print("  - Source: " + program_files_kindle)
                    print("  - Destination: " + appdata_kindle)
                    print("  - This copy will be automatically deleted after extraction")
                    print("--------------------------------------------------")
                    print()
                    return program_files_kindle, True
                else:
                    print_error("No Kindle installation found after cleanup")
                    print("--------------------------------------------------")
                    print()
                    return None, False
            except Exception as e:
                print_error(f"Failed to cleanup temp copy: {e}")
                print("--------------------------------------------------")
                print()
                return None, False
    
    # CASE 3: Only Program Files location has Kindle.exe
    elif program_files_exists:
        print_ok(f"Found Kindle at: {program_files_kindle}")
        print_warn("Kindle is installed in Program Files (Global mode)")
        print_warn("KFXKeyExtractor requires Kindle in AppData location")
        print()
        print_step("Solution: Temporary copy will be created")
        print("  - Source: " + program_files_kindle)
        print("  - Destination: " + appdata_kindle)
        print("  - This copy will be automatically deleted after extraction")
        print("--------------------------------------------------")
        print()
        return program_files_kindle, True
    
    # CASE 4: Not found in either location
    else:
        print_error("Kindle.exe not found in expected locations:")
        print(f"  - {appdata_exe}")
        print(f"  - {program_files_exe}")
        print("--------------------------------------------------")
        print()
        return None, False

def create_temp_kindle_copy(source_dir):
    """
    Create a temporary copy of Kindle installation in AppData
    Returns the path to the temporary copy
    """
    user_home = os.path.expanduser("~")
    dest_dir = os.path.join(user_home, "AppData", "Local", "Amazon", "Kindle", "application")
    temp_marker = os.path.join(dest_dir, "TEMP.txt")
    
    try:
        print_step("Creating temporary Kindle copy...")
        print(f"  Copying from: {source_dir}")
        print(f"  Copying to: {dest_dir}")
        print("  (This may take a minute...)")
        print()
        
        # Copy entire directory
        shutil.copytree(source_dir, dest_dir)
        print_ok("Kindle folder copied successfully")
        
        # Create marker file
        with open(temp_marker, 'w') as f:
            f.write(f"Temporary Kindle copy for key extraction\n")
            f.write(f"Created: {datetime.now()}\n")
            f.write(f"Source: {source_dir}\n")
        print_ok("Marker file created")
        print()
        
        return dest_dir
        
    except Exception as e:
        print_error(f"Failed to create temporary copy: {e}")
        # Cleanup partial copy if it exists
        if os.path.exists(dest_dir):
            try:
                shutil.rmtree(dest_dir)
            except:
                pass
        raise

def cleanup_temp_kindle_copy(kindle_dir):
    """
    Remove the temporary Kindle copy after extraction
    """
    temp_marker = os.path.join(kindle_dir, "TEMP.txt")
    
    # Only delete if it's a temp copy (has marker file)
    if os.path.exists(temp_marker):
        print_step("Cleaning up temporary Kindle copy...")
        try:
            shutil.rmtree(kindle_dir)
            print_ok("Temporary copy removed successfully")
        except Exception as e:
            print_error(f"Failed to cleanup temporary copy: {e}")
            print_warn(f"Please manually delete: {kindle_dir}")
        print()

def prevent_kindle_auto_update():
    """
    Create/update the 'updates' file to prevent Kindle for PC from auto-updating
    Only runs if Kindle is installed
    """
    user_home = os.path.expanduser("~")
    kindle_base = os.path.join(user_home, "AppData", "Local", "Amazon", "Kindle")
    updates_file = os.path.join(kindle_base, "updates")
    
    # Check if Kindle directory exists
    if not os.path.exists(kindle_base):
        return  # Kindle not installed, skip
    
    print_step("Configuring Kindle auto-update prevention...")
    
    try:
        # Create the updates file (no extension)
        with open(updates_file, 'w') as f:
            f.write("This file prevents Kindle for PC from auto-updating.\n")
            f.write("Created by Kindle Key Finder script.\n")
            f.write("Safe to delete if you want to allow auto-updates.\n")
        
        print_ok("Auto-update prevention file created/updated")
        print_ok(f"Location: {updates_file}")
        print("   Kindle for PC will not auto-update while this file exists")
    except Exception as e:
        print_warn(f"Could not create auto-update prevention file: {e}")
    
    print()

def fetch_book_title_from_asin(asin):
    """
    Fetch book title from ASIN using fetch-ebook-metadata command
    Returns: book title or ASIN if fetch fails
    """
    try:
        # Run fetch-ebook-metadata command
        result = subprocess.run(
            ['fetch-ebook-metadata', '-I', f'asin:{asin}'],
            capture_output=True,
            text=True,
            timeout=10,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0 and result.stdout:
            # Parse output for title
            for line in result.stdout.split('\n'):
                if line.strip().startswith('Title'):
                    # Format: "Title               : The Sunken: A Dark Steampunk Fantasy"
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        title = parts[1].strip()
                        return title if title else asin
        
        # If parsing failed, return ASIN
        return asin
        
    except Exception:
        # If command fails, return ASIN
        return asin

def scan_kindle_content_directory(content_dir):
    """
    Scan Kindle Content directory for individual book folders
    Returns: list of tuples [(asin, book_folder_path, book_title), ...]
    """
    book_folders = []
    
    try:
        if not os.path.exists(content_dir):
            print_error(f"Content directory does not exist: {content_dir}")
            return []
        
        # Scan for book folders (typically named like "B00N17VVZC_EBOK")
        for item in os.listdir(content_dir):
            item_path = os.path.join(content_dir, item)
            
            # Only process directories
            if not os.path.isdir(item_path):
                continue
            
            # Extract ASIN from folder name (e.g., "B00N17VVZC_EBOK" -> "B00N17VVZC")
            # ASIN is typically the first part before underscore
            asin = item.split('_')[0] if '_' in item else item
            
            # Try to get book title from folder metadata or use ASIN as fallback
            book_title = asin  # Default to ASIN
            
            # Check if folder contains book files (.azw, .kfx, etc.)
            has_book_files = False
            try:
                for file in os.listdir(item_path):
                    if file.lower().endswith(('.azw', '.kfx', '.kfx-zip', '.azw3')):
                        has_book_files = True
                        break
            except Exception:
                continue
            
            if has_book_files:
                book_folders.append((asin, item_path, book_title))
        
        return book_folders
        
    except Exception as e:
        print_error(f"Error scanning content directory: {e}")
        return []

def extract_keys_from_single_book(extractor_path, kindle_dir, book_folder, output_key, output_k4i, asin, book_title):
    """
    Extract keys from a single book folder using temporary directory workaround
    Returns: (success: bool, dsn: str, tokens: str, error_msg: str, asin: str)
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.join(script_dir, "temp_extraction")
    
    try:
        # Copy extractor to Kindle folder if not already there
        extractor_in_kindle = os.path.join(kindle_dir, "KFXKeyExtractor28.exe")
        if not os.path.exists(extractor_in_kindle):
            shutil.copy2(extractor_path, kindle_dir)
        
        # Create temporary directory for this book only
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Copy single book folder to temp directory
        book_name = os.path.basename(book_folder)
        temp_book = os.path.join(temp_dir, book_name)
        shutil.copytree(book_folder, temp_book)
        
        # Run extractor on temp directory (not individual book folder)
        # This gives the extractor the directory structure it expects
        process = subprocess.Popen(
            [extractor_in_kindle, temp_dir, output_key, output_k4i],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        stdout_lines = []
        stderr_lines = []
        
        # Read stderr in separate thread
        def read_stderr():
            try:
                stderr = process.stderr
                if stderr is None:
                    return
                for line in iter(stderr.readline, ''):
                    if line:
                        stderr_lines.append(line)
            except Exception:
                pass
        
        stderr_thread = threading.Thread(target=read_stderr, daemon=True)
        stderr_thread.start()
        
        # Read stdout
        try:
            stdout = process.stdout
            if stdout is not None:
                for line in iter(stdout.readline, ''):
                    if line:
                        stdout_lines.append(line)
        except Exception:
            pass
        
        # Wait for process to complete (with timeout)
        try:
            process.wait(timeout=60)  # 60 second timeout per book
        except subprocess.TimeoutExpired:
            process.kill()
            # Cleanup temp directory before returning
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return False, None, None, f"Timeout after 60 seconds", asin
        
        # Wait for stderr thread
        stderr_thread.join(timeout=5)
        
        # Check if extraction was successful
        if process.returncode != 0:
            # Combine stdout and stderr for complete error context
            stdout_text = ''.join(stdout_lines)
            stderr_text = ''.join(stderr_lines)
            
            # Filter out harmless Qt/Fontconfig messages but keep real errors
            error_lines = []
            for line in stderr_text.split('\n'):
                line_stripped = line.strip()
                if line_stripped and \
                   'QObject::startTimer' not in line and \
                   'Fontconfig error' not in line and \
                   'QThread' not in line:
                    error_lines.append(line_stripped)
            
            # If we have filtered errors, use them; otherwise generic message
            if error_lines:
                error_msg = '\n'.join(error_lines)
            else:
                # Check stdout for error messages
                if stdout_text and ('error' in stdout_text.lower() or 'failed' in stdout_text.lower()):
                    error_msg = stdout_text.strip()
                else:
                    error_msg = f"Key extraction failed (exit code {process.returncode})"
            
            # Cleanup temp directory before returning
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return False, None, None, error_msg, asin
        
        # Parse output for DSN and tokens
        dsn = None
        tokens = None
        stdout_text = ''.join(stdout_lines)
        
        if stdout_text:
            lines = stdout_text.split('\n')
            for line in lines:
                if line.startswith('DSN '):
                    dsn = line.replace('DSN ', '').strip()
                elif line.startswith('Tokens '):
                    tokens_line = line.replace('Tokens ', '').strip()
                    if ',' in tokens_line:
                        tokens = tokens_line.split(',')[0].strip()
                    else:
                        tokens = tokens_line
        
        # Check if key files were generated
        if not os.path.exists(output_key) or not os.path.exists(output_k4i):
            # Cleanup temp directory before returning
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return False, None, None, "Key files not generated", asin
        
        # Cleanup temp directory after successful extraction
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        
        return True, dsn, tokens, None, asin
        
    except Exception as e:
        # Cleanup temp directory on exception
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
        return False, None, None, str(e), asin

def append_keys_to_files(output_key, output_k4i, temp_key, temp_k4i):
    """
    Append newly extracted keys to existing key files
    Avoids duplicates by checking if keys already exist
    Returns: (success: bool, error_msg: str)
    """
    try:
        # Check if temp files exist
        if not os.path.exists(temp_key) or not os.path.exists(temp_k4i):
            return False, "Temporary key files not found"
        
        # Read new keys from temp files
        with open(temp_key, 'r') as f:
            new_key_content = f.read().strip()
        
        with open(temp_k4i, 'r') as f:
            new_k4i_content = f.read().strip()
        
        # For kindlekey.txt: Append if not duplicate
        if os.path.exists(output_key):
            with open(output_key, 'r') as f:
                existing_key_content = f.read()
            
            # Check if this key already exists
            if new_key_content not in existing_key_content:
                with open(output_key, 'a') as f:
                    f.write('\n' + new_key_content)
        else:
            # Create new file
            with open(output_key, 'w') as f:
                f.write(new_key_content)
        
        # For kindlekey.k4i: Merge JSON data
        if os.path.exists(output_k4i):
            with open(output_k4i, 'r') as f:
                existing_k4i = json.load(f)
            
            new_k4i = json.loads(new_k4i_content)
            
            # Merge secrets arrays (avoid duplicates)
            for key in ['kindle.account.secrets', 'kindle.account.new_secrets', 'kindle.account.clear_old_secrets']:
                if key in new_k4i:
                    if key not in existing_k4i:
                        existing_k4i[key] = []
                    for item in new_k4i[key]:
                        if item not in existing_k4i[key]:
                            existing_k4i[key].append(item)
            
            # Update DSN if present
            if 'DSN' in new_k4i and new_k4i['DSN']:
                existing_k4i['DSN'] = new_k4i['DSN']
            
            # Update tokens if present
            if 'kindle.account.tokens' in new_k4i and new_k4i['kindle.account.tokens']:
                existing_k4i['kindle.account.tokens'] = new_k4i['kindle.account.tokens']
            
            # Write merged data
            with open(output_k4i, 'w') as f:
                json.dump(existing_k4i, f, indent=2)
        else:
            # Create new file
            with open(output_k4i, 'w') as f:
                f.write(new_k4i_content)
        
        return True, ""
        
    except Exception as e:
        return False, str(e)

def write_extraction_log(extraction_stats, script_dir):
    """
    Write detailed extraction log to file
    Returns: log file path
    """
    # Create logs directory with extraction subfolder
    logs_dir = os.path.join(script_dir, "Logs", "extraction_logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"extraction_{timestamp}.log")
    
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 70 + "\n")
            f.write("KINDLE KEY EXTRACTION LOG\n")
            f.write("=" * 70 + "\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Books Found: {extraction_stats['total']}\n")
            f.write(f"Timeout per book: 60 seconds\n")
            f.write("\n")
            
            # Failed extractions section
            if extraction_stats.get('failed_books'):
                f.write("-" * 70 + "\n")
                f.write(f"FAILED EXTRACTIONS ({len(extraction_stats['failed_books'])})\n")
                f.write("-" * 70 + "\n")
                for asin, title, error_msg in extraction_stats['failed_books']:
                    f.write(f"\n[FAILED] {asin} - {title}\n")
                    f.write(f"  Error: {error_msg}\n")
                f.write("\n")
            
            # Success section (summary only)
            if extraction_stats['success'] > 0:
                f.write("-" * 70 + "\n")
                f.write(f"SUCCESSFUL EXTRACTIONS ({extraction_stats['success']})\n")
                f.write("-" * 70 + "\n")
                f.write(f"Keys successfully extracted from {extraction_stats['success']} book(s)\n")
                f.write("\n")
            
            # Summary
            f.write("=" * 70 + "\n")
            f.write("SUMMARY\n")
            f.write("=" * 70 + "\n")
            f.write(f"Total:    {extraction_stats['total']}\n")
            f.write(f"Success:  {extraction_stats['success']}\n")
            f.write(f"Failed:   {extraction_stats['failed']}\n")
            f.write("=" * 70 + "\n")
        
        return log_file
        
    except Exception as e:
        print_warn(f"Failed to write extraction log file: {e}")
        return None

def extract_keys_using_extractor(extractor_path, content_dir, output_key, output_k4i):
    """
    Extract keys using the KFXKeyExtractor28.exe with per-book processing
    Returns: (success: bool, dsn: str, tokens: str, extraction_stats: dict)
    """
    # Find kindle.exe location
    kindle_dir, needs_temp_copy = find_kindle_exe()
    
    if not kindle_dir:
        raise FileNotFoundError("Kindle for PC installation not found. Please install Kindle for PC.")
    
    temp_copy_created = False
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Initialize extraction statistics
    extraction_stats = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'failed_books': []  # List of tuples: (asin, title, error_msg)
    }
    
    # Load config to check if book title fetching is enabled
    config = load_config()
    fetch_titles = config.get('fetch_book_titles', False) if config else False
    
    try:
        # Create temporary copy if needed
        if needs_temp_copy:
            kindle_dir = create_temp_kindle_copy(kindle_dir)
            temp_copy_created = True
        
        # Scan for individual book folders
        print_step("Scanning for book folders...")
        book_folders = scan_kindle_content_directory(content_dir)
        
        if not book_folders:
            print_warn("No book folders found in content directory")
            print()
            return False, None, None, extraction_stats
        
        extraction_stats['total'] = len(book_folders)
        print_ok(f"Found {len(book_folders)} book folder(s)")
        print()
        
        # Process each book individually
        print_step(f"Extracting keys from {len(book_folders)} book(s)...")
        print()
        
        # Create temporary key files for per-book extraction
        temp_key = output_key + ".temp"
        temp_k4i = output_k4i + ".temp"
        
        dsn = None
        tokens = None
        
        for idx, (asin, book_folder, book_title) in enumerate(book_folders, 1):
            # Get folder name (e.g., "B00JBVUJM8_EBOK")
            folder_name = os.path.basename(book_folder)
            
            # Fetch book title from Amazon metadata only if enabled
            if fetch_titles:
                fetched_title = fetch_book_title_from_asin(asin)
                # Display: folder_name - book_title
                print(f"[{idx}/{len(book_folders)}] {folder_name} - {fetched_title}...", end=' ', flush=True)
            else:
                # Display: folder_name only
                print(f"[{idx}/{len(book_folders)}] {folder_name}...", end=' ', flush=True)
            
            # Extract keys from single book
            success, book_dsn, book_tokens, error_msg, _ = extract_keys_from_single_book(
                extractor_path, kindle_dir, book_folder, temp_key, temp_k4i, asin, book_title
            )
            
            if success:
                print_ok("✓")
                extraction_stats['success'] += 1
                
                # Store DSN and tokens from first successful extraction
                if not dsn and book_dsn:
                    dsn = book_dsn
                if not tokens and book_tokens:
                    tokens = book_tokens
                
                # Append keys to main files
                append_success, append_error = append_keys_to_files(output_key, output_k4i, temp_key, temp_k4i)
                if not append_success:
                    print_warn(f" (Warning: Failed to append keys - {append_error})")
                
                # Cleanup temp files
                try:
                    if os.path.exists(temp_key):
                        os.remove(temp_key)
                    if os.path.exists(temp_k4i):
                        os.remove(temp_k4i)
                except Exception:
                    pass
            else:
                print_error(f"✗ FAILED")
                extraction_stats['failed'] += 1
                
                # Fetch book title from ASIN for better error reporting
                fetched_title = fetch_book_title_from_asin(asin)
                extraction_stats['failed_books'].append((asin, fetched_title, error_msg if error_msg else "Unknown error"))
        
        print()
        
        # Cleanup extractor from Kindle folder
        extractor_in_kindle = os.path.join(kindle_dir, "KFXKeyExtractor28.exe")
        if os.path.exists(extractor_in_kindle):
            os.remove(extractor_in_kindle)
            print_ok("Extractor cleaned up from Kindle folder")
        
        # Write extraction log if there were failures
        if extraction_stats['failed'] > 0:
            log_file = write_extraction_log(extraction_stats, script_dir)
            if log_file:
                print_step(f"Extraction error log saved to:")
                print(f"      {log_file}")
        
        print()
        
        # Check if extraction was successful (at least one book succeeded)
        overall_success = extraction_stats['success'] > 0
        
        return overall_success, dsn, tokens, extraction_stats
        
    except Exception as e:
        print_error(f"Extractor method failed: {e}")
        return False, None, None, extraction_stats
        
    finally:
        # Always cleanup temporary copy if we created one
        if temp_copy_created:
            cleanup_temp_kindle_copy(kindle_dir)

def create_kindle_key_from_k4i(k4i_path, dsn=None, tokens=None):
    """
    Create a Kindle key entry exactly like the DeDRM plugin does
    This replicates the logic from kindlekey.py's kindlekeys() function
    Handles missing fields gracefully with extracted or default values
    """
    try:
        with open(k4i_path, 'r') as f:
            k4i_data = json.load(f)
        
        # Handle missing fields by providing defaults or extracted values
        kindle_key = {
            "DSN": k4i_data.get("DSN", dsn or ""),
            "kindle.account.clear_old_secrets": k4i_data.get("kindle.account.clear_old_secrets", []),
            "kindle.account.new_secrets": k4i_data.get("kindle.account.new_secrets", []), 
            "kindle.account.secrets": k4i_data.get("kindle.account.secrets", []),
            "kindle.account.tokens": k4i_data.get("kindle.account.tokens", tokens or "")
        }
        
        return kindle_key
        
    except Exception as e:
        print_error(f"Failed to process k4i file: {e}")
        return None

def create_dedrm_config(kindle_key, kindlekey_txt_path, reference_json_path=None):
    """
    Create the dedrm.json configuration exactly like the plugin does
    """
    
    if reference_json_path and os.path.exists(reference_json_path):
        # Use reference file as template
        print_step("Using reference file as template...")
        with open(reference_json_path, 'r') as f:
            dedrm_config = json.load(f)
    else:
        # Create new structure matching plugin's default
        print_step("Creating new configuration structure...")
        dedrm_config = {
            "adeptkeys": {},
            "adobe_pdf_passphrases": [],
            "adobewineprefix": "",
            "androidkeys": {},
            "bandnkeys": {},
            "configured": True,
            "deobfuscate_fonts": True,
            "ereaderkeys": {},
            "kindleextrakeyfile": "",
            "kindlekeys": {},
            "kindlewineprefix": "",
            "lcp_passphrases": [],
            "pids": [],
            "remove_watermarks": False,
            "serials": []
        }
    
    # Set the extra key file path (with proper escaping for JSON)
    dedrm_config["kindleextrakeyfile"] = kindlekey_txt_path
    
    # Add the kindle key exactly like the plugin does
    # The plugin uses the key name "kindlekey" + count, but for single key we use "kindlekey"
    dedrm_config["kindlekeys"]["kindlekey"] = kindle_key
    
    return dedrm_config

# ============================================================================
# UNIFIED CONFIGURATION FUNCTIONS
# ============================================================================

def load_config():
    """
    Load unified configuration from JSON file
    Returns dict or None if file doesn't exist
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, CONFIG_FILE)
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            print_warn(f"Failed to load configuration: {e}")
            return None
    return None

def save_config(config):
    """
    Save unified configuration to JSON file
    Returns True if successful, False otherwise
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, CONFIG_FILE)
    
    try:
        # Add script version and timestamp (type: ignore for mixed dict types)
        config['script_version'] = SCRIPT_VERSION  # type: ignore
        config['last_updated'] = datetime.now().isoformat()  # type: ignore
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print_ok(f"Configuration saved to: {config_path}")
        return True
    except Exception as e:
        print_error(f"Failed to save configuration: {e}")
        return False

def check_config_version(config):
    """
    Check if config version matches current script version
    Returns: (is_valid: bool, config_version: str, current_version: str)
    """
    config_version = config.get('script_version', 'Unknown')
    is_valid = (config_version == SCRIPT_VERSION)
    return is_valid, config_version, SCRIPT_VERSION

def delete_config():
    """Delete configuration file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, CONFIG_FILE)
    
    try:
        if os.path.exists(config_path):
            os.remove(config_path)
            print_ok("Configuration deleted")
            return True
        return False
    except Exception as e:
        print_error(f"Failed to delete configuration: {e}")
        return False

def display_config_summary(config):
    """Display configuration summary in table format"""
    print_step("Current Configuration:")
    print()
    
    # Table header (wider to accommodate long paths - 72 chars for value column)
    print("┌─────────────────────────────┬──────────────────────────────────────────────────────────────────────────┐")
    print("│ Setting                     │ Value                                                                    │")
    print("├─────────────────────────────┼──────────────────────────────────────────────────────────────────────────┤")
    
    # Kindle Content Path
    content_path = config.get('kindle_content_path', 'Not set')
    if len(content_path) > 72:
        content_path = content_path[:69] + "..."
    print(f"│ Kindle Content Path         │ {content_path:<72} │")
    
    # Hide Sensitive Info
    hide_sensitive = "Yes" if config.get('hide_sensitive_info', False) else "No"
    print(f"│ Hide Sensitive Info         │ {hide_sensitive:<72} │")
    
    # Fetch Book Titles
    fetch_titles = "Yes" if config.get('fetch_book_titles', False) else "No"
    print(f"│ Fetch Book Titles           │ {fetch_titles:<72} │")
    
    # Clear Screen Between Phases
    clear_screen = "Yes" if config.get('clear_screen_between_phases', True) else "No"
    print(f"│ Clear Screen Between Phases │ {clear_screen:<72} │")
    
    # Skip Phase Pauses
    skip_pauses = "Yes" if config.get('skip_phase_pauses', False) else "No"
    print(f"│ Skip Phase Pauses           │ {skip_pauses:<72} │")
    
    # Calibre Import section
    if 'calibre_import' in config:
        cal = config['calibre_import']
        calibre_status = "Enabled" if cal.get('enabled') else "Disabled"
        print(f"│ Calibre Import              │ {calibre_status:<72} │")
        
        if cal.get('enabled'):
            # Library Path with book count
            lib_path = cal.get('library_path', 'Not set')
            
            # Try to get book count
            book_count = get_library_book_count(lib_path) if lib_path != 'Not set' else None
            
            # Format display with book count
            if book_count is not None:
                display_path = f"{lib_path} ({book_count} books)"
            else:
                display_path = f"{lib_path} (Unknown books)"
            
            if len(display_path) > 72:
                display_path = display_path[:69] + "..."
            print(f"│   Library Path              │ {display_path:<72} │")
            
            # Convert to EPUB
            convert_epub = "Yes" if cal.get('convert_to_epub', False) else "No"
            print(f"│   Convert to EPUB           │ {convert_epub:<72} │")
            
            # KFX-ZIP Handling
            kfx_mode = cal.get('kfx_zip_mode', 'convert_all')
            kfx_mode_display = {
                'convert_all': 'Convert All (including .kfx-zip)',
                'skip_kfx_zip': 'Skip .kfx-zip files',
                'convert_regular_only': 'Convert regular .kfx only'
            }.get(kfx_mode, kfx_mode)
            print(f"│   KFX-ZIP Handling          │ {kfx_mode_display:<72} │")
            
            # Source Management
            source_mgmt = cal.get('source_file_management', 'keep_both')
            source_mgmt_display = {
                'keep_both': 'Keep Both (Source + EPUB)',
                'delete_source': 'Delete Source after conversion',
                'delete_kfx_zip_only': 'Delete .kfx-zip only'
            }.get(source_mgmt, source_mgmt)
            print(f"│   Source Management         │ {source_mgmt_display:<72} │")
    else:
        print(f"│ Calibre Import              │ {'Not configured':<72} │")
    
    # Table footer
    print("└─────────────────────────────┴──────────────────────────────────────────────────────────────────────────┘")
    print()

def prompt_config_action_with_timer(config):
    """Display config and timer with interrupt capability"""
    print_step("Configuration Found")
    print("--------------------------------------------------")
    display_config_summary(config)
    
    # Validate Calibre library path if Calibre import is enabled
    if 'calibre_import' in config and config['calibre_import'].get('enabled', False):
        lib_path = config['calibre_import'].get('library_path')
        if lib_path:
            print_step("Validating saved Calibre library path...")
            valid, error, book_count = verify_library_path(lib_path)
            
            if not valid:
                print()
                print_error("SAVED LIBRARY PATH IS INVALID!")
                print(f"  Path: {lib_path}")
                print(f"  Error: {error}")
                print()
                print_warn("The saved Calibre library path is no longer valid.")
                print("This could happen if:")
                print("  - Library was deleted or moved")
                print("  - Network drive is disconnected")
                print("  - Running on different machine")
                print("  - metadata.db was removed or corrupted")
                print()
                print("Options:")
                print("  [R] Reconfigure - Update library path")
                print("  [D] Disable - Turn off Calibre import")
                print("  [Q] Quit - Exit script")
                print()
                
                while True:
                    choice = input("Your choice (R/D/Q): ").strip().upper()
                    if choice == 'R':
                        print()
                        return 'reconfigure'
                    elif choice == 'D':
                        print()
                        print_step("Disabling Calibre import...")
                        config['calibre_import']['enabled'] = False
                        save_config(config)
                        print_ok("Calibre import disabled")
                        print()
                        return 'use'
                    elif choice == 'Q':
                        print()
                        return 'quit'
                    else:
                        print_error("Invalid choice. Please enter R, D, or Q.")
            else:
                if book_count is not None:
                    print_ok(f"Library path validated: {book_count} books found")
                else:
                    print_ok("Library path validated")
                print()
    
    # Check if pauses should be skipped to adjust countdown time
    skip_pauses = config.get('skip_phase_pauses', False)
    countdown_seconds = 3 if skip_pauses else 10
    
    print(f"Press any key to show options, or wait {countdown_seconds} seconds to use saved configuration...")
    print()
    
    timer_cancelled = threading.Event()
    user_interrupted = threading.Event()
    countdown_active = True
    
    def countdown_timer():
        nonlocal countdown_active
        for i in range(countdown_seconds, 0, -1):
            if timer_cancelled.is_set() or user_interrupted.is_set():
                countdown_active = False
                return
            print(f"\rCountdown: {i} seconds... ", end='', flush=True)
            time.sleep(1)
        countdown_active = False
        if not user_interrupted.is_set():
            print("\r" + " " * 50 + "\r", end='', flush=True)
            print_ok("Auto-proceeding with saved configuration")
            timer_cancelled.set()
    
    timer_thread = threading.Thread(target=countdown_timer, daemon=True)
    timer_thread.start()
    
    while countdown_active:
        if msvcrt.kbhit():
            msvcrt.getch()
            user_interrupted.set()
            timer_cancelled.set()
            print("\r" + " " * 50 + "\r", end='', flush=True)
            break
        time.sleep(0.05)
    
    if not user_interrupted.is_set():
        return 'use'
    
    print()
    print_step("Configuration Options:")
    print("  [U] Use saved configuration")
    print("  [R] Reconfigure settings")
    print("  [D] Delete saved config and reconfigure")
    print("  [Q] Quit script")
    print()
    
    while True:
        choice = input("Your choice (U/R/D/Q): ").strip().upper()
        if choice == 'U':
            print()
            return 'use'
        elif choice == 'R':
            print()
            return 'reconfigure'
        elif choice == 'D':
            print()
            delete_config()
            return 'reconfigure'
        elif choice == 'Q':
            print()
            return 'quit'
        else:
            print_error("Invalid choice. Please enter U, R, D, or Q.")

# ============================================================================
# PRE-FLIGHT CONFIGURATION WIZARD
# ============================================================================

def configure_pre_flight_wizard(user_home):
    """
    Pre-Flight Configuration Wizard
    Comprehensive setup for all script options
    """
    os.system('cls')
    print()
    print_banner_and_version()
    print("=" * 70)
    print_step("PRE-FLIGHT CONFIGURATION WIZARD")
    print("=" * 70)
    print()
    print("This wizard will guide you through configuring all script options.")
    print("You can change these settings later by deleting the config file.")
    print()
    
    config = {
        'script_version': SCRIPT_VERSION,
        'last_updated': datetime.now().isoformat()
    }
    
    # 1. Kindle Content Path
    print_step("[1/5] Kindle Content Directory")
    print("--------------------------------------------------")
    default_content = os.path.join(user_home, "Documents", "My Kindle Content")
    print(f"Default: {default_content}")
    print()
    
    while True:
        choice = input("Use default path? (Y/N) [Y]: ").strip().upper()
        if choice == '':
            choice = 'Y'  # Default to Yes
        if choice == 'Y':
            config['kindle_content_path'] = default_content
            print()
            print_ok(f"✓ Using: {default_content}")
            break
        elif choice == 'N':
            custom_path = input("Enter custom path: ").strip().strip('"').strip("'")
            custom_path = os.path.normpath(os.path.expandvars(custom_path))
            if os.path.exists(custom_path):
                config['kindle_content_path'] = custom_path
                print()
                print_ok(f"✓ Using: {custom_path}")
                break
            else:
                print_error("Path does not exist. Try again.")
        else:
            print_error("Please enter Y or N")
    
    print()
    
    # Clear console before next question
    os.system('cls')
    print()
    print_banner_and_version()
    print("=" * 70)
    print_step("PRE-FLIGHT CONFIGURATION WIZARD")
    print("=" * 70)
    print()
    print_ok(f"✓ [1/5] Kindle Content Path: {config['kindle_content_path']}")
    print()
    
    # 2. Hide Sensitive Information
    print_step("[2/5] Privacy Settings")
    print("--------------------------------------------------")
    print("Hide sensitive information (DSN, tokens, keys) in console output?")
    print()
    
    while True:
        choice = input("Hide sensitive info? (Y/N) [Y]: ").strip().upper()
        if choice == '':
            choice = 'Y'  # Default to Yes
        if choice in ['Y', 'N']:
            config['hide_sensitive_info'] = (choice == 'Y')  # type: ignore
            print()
            if choice == 'Y':
                print_ok("✓ Sensitive information will be hidden")
            else:
                print_ok("✓ Sensitive information will be shown")
            break
        print_error("Please enter Y or N")
    
    print()
    
    # Clear console before next question
    os.system('cls')
    print()
    print_banner_and_version()
    print("=" * 70)
    print_step("PRE-FLIGHT CONFIGURATION WIZARD")
    print("=" * 70)
    print()
    print_ok(f"✓ [1/5] Kindle Content Path: {config['kindle_content_path']}")
    hide_status = "Yes" if config['hide_sensitive_info'] else "No"
    print_ok(f"✓ [2/5] Hide Sensitive Info: {hide_status}")
    print()
    
    # 3. Fetch Book Titles During Key Extraction
    print_step("[3/5] Key Extraction Display Options")
    print("--------------------------------------------------")
    print("Fetch book titles from Amazon during key extraction?")
    print()
    print_warn("NOTE:")
    print("  - Fetching titles queries Amazon servers for each book")
    print("  - This will significantly slow down the extraction process")
    print("  - Titles are only used for display purposes during extraction")
    print("  - Recommended: No (faster extraction)")
    print()
    
    while True:
        choice = input("Fetch book titles during extraction? (Y/N) [N]: ").strip().upper()
        if choice == '':
            choice = 'N'  # Default to No (faster)
        if choice in ['Y', 'N']:
            config['fetch_book_titles'] = (choice == 'Y')  # type: ignore
            print()
            if choice == 'Y':
                print_ok("✓ Book titles will be fetched (slower extraction)")
            else:
                print_ok("✓ Book titles will NOT be fetched (faster extraction)")
            break
        print_error("Please enter Y or N")
    
    print()
    
    # Clear console before next question
    os.system('cls')
    print()
    print_banner_and_version()
    print("=" * 70)
    print_step("PRE-FLIGHT CONFIGURATION WIZARD")
    print("=" * 70)
    print()
    print_ok(f"✓ [1/5] Kindle Content Path: {config['kindle_content_path']}")
    hide_status = "Yes" if config['hide_sensitive_info'] else "No"
    print_ok(f"✓ [2/5] Hide Sensitive Info: {hide_status}")
    fetch_status = "Yes" if config['fetch_book_titles'] else "No"
    print_ok(f"✓ [3/5] Fetch Book Titles: {fetch_status}")
    print()
    
    # 4. Clear Screen Between Phases
    print_step("[4/6] Display Options")
    print("--------------------------------------------------")
    print("Clear screen between each phase for cleaner output?")
    print()
    print_warn("NOTE:")
    print("  - Clearing screen provides a cleaner, less cluttered view")
    print("  - Each phase will start with a fresh screen")
    print("  - Phase summaries will still be displayed before clearing")
    print("  - Recommended: Yes (cleaner output)")
    print()
    
    while True:
        choice = input("Clear screen between phases? (Y/N) [Y]: ").strip().upper()
        if choice == '':
            choice = 'Y'  # Default to Yes
        if choice in ['Y', 'N']:
            config['clear_screen_between_phases'] = (choice == 'Y')  # type: ignore
            print()
            if choice == 'Y':
                print_ok("✓ Screen will be cleared between phases")
            else:
                print_ok("✓ Screen will NOT be cleared between phases")
            break
        print_error("Please enter Y or N")
    
    print()
    
    # Clear console before next question
    os.system('cls')
    print()
    print_banner_and_version()
    print("=" * 70)
    print_step("PRE-FLIGHT CONFIGURATION WIZARD")
    print("=" * 70)
    print()
    print_ok(f"✓ [1/6] Kindle Content Path: {config['kindle_content_path']}")
    hide_status = "Yes" if config['hide_sensitive_info'] else "No"
    print_ok(f"✓ [2/6] Hide Sensitive Info: {hide_status}")
    fetch_status = "Yes" if config['fetch_book_titles'] else "No"
    print_ok(f"✓ [3/6] Fetch Book Titles: {fetch_status}")
    clear_status = "Yes" if config['clear_screen_between_phases'] else "No"
    print_ok(f"✓ [4/6] Clear Screen Between Phases: {clear_status}")
    print()
    
    # 5. Skip Phase Pauses
    print_step("[5/6] Phase Pause Settings")
    print("--------------------------------------------------")
    print("Skip countdown pauses between phases for faster execution?")
    print()
    print_warn("NOTE:")
    print("  - Pauses allow you to review phase summaries before continuing")
    print("  - Skipping pauses makes the script run faster without interruption")
    print("  - Initial config review pause will be reduced to 3 seconds (from 10)")
    print("  - Phase summaries will still be displayed even if pauses are skipped")
    print("  - Recommended: No (keep pauses for better visibility)")
    print()
    
    while True:
        choice = input("Skip phase pauses? (Y/N) [N]: ").strip().upper()
        if choice == '':
            choice = 'N'  # Default to No (keep pauses)
        if choice in ['Y', 'N']:
            config['skip_phase_pauses'] = (choice == 'Y')  # type: ignore
            print()
            if choice == 'Y':
                print_ok("✓ Phase pauses will be skipped (faster execution)")
            else:
                print_ok("✓ Phase pauses will be shown (better visibility)")
            break
        print_error("Please enter Y or N")
    
    print()
    
    # Clear console before next question
    os.system('cls')
    print()
    print_banner_and_version()
    print("=" * 70)
    print_step("PRE-FLIGHT CONFIGURATION WIZARD")
    print("=" * 70)
    print()
    print_ok(f"✓ [1/6] Kindle Content Path: {config['kindle_content_path']}")
    hide_status = "Yes" if config['hide_sensitive_info'] else "No"
    print_ok(f"✓ [2/6] Hide Sensitive Info: {hide_status}")
    fetch_status = "Yes" if config['fetch_book_titles'] else "No"
    print_ok(f"✓ [3/6] Fetch Book Titles: {fetch_status}")
    clear_status = "Yes" if config['clear_screen_between_phases'] else "No"
    print_ok(f"✓ [4/6] Clear Screen Between Phases: {clear_status}")
    skip_pauses_status = "Yes" if config['skip_phase_pauses'] else "No"
    print_ok(f"✓ [5/6] Skip Phase Pauses: {skip_pauses_status}")
    print()
    
    # 6. Calibre Import Settings
    print_step("[6/6] Calibre Auto-Import")
    print("--------------------------------------------------")
    print("Enable automatic import of DeDRMed ebooks to Calibre?")
    print("(You can configure this later if you skip now)")
    print()
    
    while True:
        choice = input("Configure Calibre import now? (Y/N) [Y]: ").strip().upper()
        if choice == '':
            choice = 'Y'  # Default to Yes
        if choice in ['Y', 'N']:
            break
        print_error("Please enter Y or N")
    
    if choice == 'N':
        config['calibre_import'] = {'enabled': False}  # type: ignore
        print()
        print_ok("✓ Calibre auto-import disabled")
        print()
        print()
    else:
        print()
        calibre_config = prompt_calibre_import_settings()
        if calibre_config:
            config['calibre_import'] = calibre_config  # type: ignore
        else:
            config['calibre_import'] = {'enabled': False}  # type: ignore
    
    # Display final configuration review
    while True:
        # Clear console before showing review
        os.system('cls')
        print()
        print_banner_and_version()
        print("=" * 70)
        print_step("CONFIGURATION REVIEW")
        print("=" * 70)
        print()
        print("Please review your configuration before saving:")
        print()
        display_config_summary(config)
        
        print("Options:")
        print("  [Y] Yes, save and continue (recommended)")
        print("  [R] Reconfigure - Start over")
        print("  [Q] Quit without saving")
        print()
        
        review_choice = input("Your choice (Y/R/Q) [Y]: ").strip().upper()
        if review_choice == '':
            review_choice = 'Y'
        
        if review_choice == 'Y':
            # Save configuration
            print()
            print_step("Saving Configuration")
            print("--------------------------------------------------")
            save_config(config)
            print()
            
            print("=" * 70)
            print_done("PRE-FLIGHT CONFIGURATION COMPLETE")
            print("=" * 70)
            print()
            
            return config
        elif review_choice == 'R':
            print()
            print_step("Restarting configuration wizard...")
            print()
            # Recursively call the wizard to start over
            return configure_pre_flight_wizard(user_home)
        elif review_choice == 'Q':
            print()
            print_warn("Configuration cancelled - exiting without saving")
            sys.exit(0)
        else:
            print_error("Invalid choice. Please enter Y, R, or Q.")

# ============================================================================
# CALIBRE AUTO-IMPORT FUNCTIONS
# ============================================================================

def load_calibre_config():
    """
    Load saved Calibre import configuration from JSON file (legacy support)
    Returns dict or None if file doesn't exist
    """
    # Try new unified config first
    config = load_config()
    if config and 'calibre' in config:
        return config['calibre']
    
    # Fall back to old calibre_import_config.json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "calibre_import_config.json")
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            print_warn(f"Failed to load saved configuration: {e}")
            return None
    return None

def save_calibre_config(config):
    """
    Save Calibre import configuration to JSON file (legacy support)
    Returns True if successful, False otherwise
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "calibre_import_config.json")
    
    try:
        # Add timestamp
        config['last_updated'] = datetime.now().isoformat()
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print_ok(f"Configuration saved to: {config_path}")
        return True
    except Exception as e:
        print_error(f"Failed to save configuration: {e}")
        return False

def display_saved_config(config):
    """
    Display saved configuration
    """
    print_step("Saved Calibre Import Configuration:")
    print(f"  Library Path: {config.get('library_path', 'Not set')}")
    print()

def prompt_calibre_with_timer(saved_config):
    """
    Display saved config and 5-second timer with interrupt capability
    Returns: 'use' | 'reconfigure' | 'skip' | 'delete'
    """
    print_step("Calibre Auto-Import Configuration Found")
    print("--------------------------------------------------")
    display_saved_config(saved_config)
    
    print("Press any key to show options, or wait 5 seconds to use saved configuration...")
    print()
    
    # Shared state for timer and input
    timer_cancelled = threading.Event()
    user_interrupted = threading.Event()
    countdown_active = True
    
    def countdown_timer():
        nonlocal countdown_active
        for i in range(5, 0, -1):
            if timer_cancelled.is_set() or user_interrupted.is_set():
                countdown_active = False
                return
            print(f"\rCountdown: {i} seconds... ", end='', flush=True)
            time.sleep(1)
        countdown_active = False
        if not user_interrupted.is_set():
            print("\r" + " " * 50 + "\r", end='', flush=True)
            print_ok("Auto-proceeding with saved configuration")
            timer_cancelled.set()
    
    # Start countdown timer
    timer_thread = threading.Thread(target=countdown_timer, daemon=True)
    timer_thread.start()
    
    # Wait for user input or timer expiry
    while countdown_active:
        if msvcrt.kbhit():
            # User pressed a key - cancel timer and show menu
            msvcrt.getch()  # Consume the keypress
            user_interrupted.set()
            timer_cancelled.set()
            print("\r" + " " * 50 + "\r", end='', flush=True)
            break
        time.sleep(0.05)
    
    # If timer expired without interruption, use saved config
    if not user_interrupted.is_set():
        return 'use'
    
    # Show menu
    print()
    print_step("Configuration Options:")
    print("  [U] Use saved configuration")
    print("  [R] Reconfigure settings")
    print("  [S] Skip auto-import this time")
    print("  [D] Delete saved config and skip")
    print()
    
    while True:
        choice = input("Your choice (U/R/S/D): ").strip().upper()
        if choice == 'U':
            print()
            return 'use'
        elif choice == 'R':
            print()
            return 'reconfigure'
        elif choice == 'S':
            print()
            return 'skip'
        elif choice == 'D':
            print()
            return 'delete'
        else:
            print_error("Invalid choice. Please enter U, R, S, or D.")

def get_last_calibre_library():
    """
    Read last library from Calibre's global.py.json
    Returns: library_path or None if not found
    """
    try:
        config_file = os.path.join(
            os.path.expanduser("~"),
            "AppData", "Roaming", "calibre", "global.py.json"
        )
        
        if not os.path.exists(config_file):
            return None
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        return config.get('library_path')
        
    except Exception as e:
        print_warn(f"Could not read Calibre config: {e}")
        return None

def get_library_book_count(library_path):
    """
    Get the total number of books in a Calibre library
    Returns: book_count (int) or None if query fails
    """
    import sqlite3
    
    try:
        db_path = os.path.join(library_path, "metadata.db")
        conn = sqlite3.connect(db_path, timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM books")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return None  # Return None on any error

def verify_library_path(library_path):
    """
    Verify library path exists and contains metadata.db
    Returns: (valid: bool, error_message: str, book_count: int or None)
    """
    if not os.path.exists(library_path):
        return False, "Library path does not exist", None
    
    metadata_db = os.path.join(library_path, "metadata.db")
    if not os.path.exists(metadata_db):
        return False, "Not a valid Calibre library (metadata.db not found)", None
    
    # Get book count
    book_count = get_library_book_count(library_path)
    
    return True, "", book_count

def prompt_manual_library_path():
    """
    Prompt user to manually enter library path
    Returns: validated library path
    """
    print_step("Enter Calibre Library Path")
    print("This is the folder containing metadata.db")
    print("Example: D:\\OneDrive\\Calibre-Libraries\\Temp-downloads")
    print()
    
    while True:
        library_path = input("Library path: ").strip().strip('"').strip("'")
        
        if not library_path:
            print_error("Path cannot be empty")
            continue
        
        # Normalize path
        library_path = os.path.normpath(library_path)
        
        # Verify it's valid
        valid, error, book_count = verify_library_path(library_path)
        
        if valid:
            print_ok(f"Library path validated: {library_path}")
            if book_count is not None:
                print(f"  Books found: {book_count}")
            else:
                print(f"  Books found: Unknown")
            print()
            return library_path
        else:
            print_error(f"Invalid library path: {error}")
            print()
            retry = input("Try again? (Y/N): ").strip().upper()
            if retry != 'Y':
                raise Exception("Library path validation cancelled")

def get_and_confirm_library_path():
    """
    Get library path with fallback to manual entry
    Returns: validated library path
    """
    # Try to read last library from Calibre config
    last_library = get_last_calibre_library()
    
    if last_library:
        # Get book count for display
        book_count = get_library_book_count(last_library)
        if book_count is not None:
            print_ok(f"Last used Calibre library: {last_library} ({book_count} books)")
        else:
            print_ok(f"Last used Calibre library: {last_library}")
        print()
        choice = input("Use this library? (Y/N) [Y]: ").strip().upper()
        if choice == '':
            choice = 'Y'  # Default to Yes
        
        if choice == 'Y':
            # Verify it's valid
            valid, error, book_count = verify_library_path(last_library)
            if valid:
                if book_count is not None:
                    print_ok(f"Library validated: {book_count} books found")
                else:
                    print_ok(f"Library validated: Unknown book count")
                print()
                return last_library
            else:
                print_warn(f"Library path invalid: {error}")
                print_warn("Please enter a valid library path")
                print()
    else:
        print_warn("Could not find Calibre configuration")
        print_warn("Please enter your Calibre library path manually")
        print()
    
    # Fallback: Manual entry
    return prompt_manual_library_path()

def prompt_calibre_import_settings():
    """
    Prompt user for Calibre import settings
    Returns: dict with configuration or None if user declines
    """
    # Track configuration progress
    config_progress = {}
    
    # Initial screen
    os.system('cls')
    print()
    print_banner_and_version()
    print("=" * 70)
    print_step("PRE-FLIGHT CONFIGURATION WIZARD")
    print("=" * 70)
    print()
    print_step("[6/6] Calibre Auto-Import")
    print("--------------------------------------------------")
    print()
    
    # Check if Calibre is running
    if not is_calibre_running():
        print_ok("Calibre not detected as Running - proceeding automatically")
        print()
    else:
        # Important: Calibre must be closed to read configuration files
        print_warn("IMPORTANT: Please close Calibre now before proceeding")
        print()
        print("During configuration, the script needs to read Calibre's configuration")
        print("files to detect your last used library path. This requires Calibre to")
        print("be completely closed.")
        print()
        
        input("Press Enter once Calibre is closed to continue...")
        print()
        
        # VERIFY closure with retry loop
        if not verify_calibre_closed_with_loop():
            raise Exception("Configuration cancelled - Calibre must be closed")
    
    # Get and confirm library path
    library_path = get_and_confirm_library_path()
    config_progress['library_path'] = library_path
    
    # Get book count for display
    book_count = get_library_book_count(library_path)
    config_progress['book_count'] = book_count
    
    # Clear screen and show progress before EPUB conversion question
    os.system('cls')
    print()
    print_banner_and_version()
    print("=" * 70)
    print_step("PRE-FLIGHT CONFIGURATION WIZARD")
    print("=" * 70)
    print()
    print_ok(f"✓ [6/6] Calibre Auto-Import")
    if book_count is not None:
        print(f"  ✓ Library Path: {config_progress['library_path']} ({book_count} books)")
    else:
        print(f"  ✓ Library Path: {config_progress['library_path']}")
    print()
    
    # Ask about Imported eBook to EPUB conversion
    print_step("Imported eBook to EPUB Conversion")
    print("--------------------------------------------------")
    print()
    print("After importing ebooks, they can be automatically converted to EPUB format.")
    print()
    print_warn("NOTES:")
    print("  - Conversion uses ebook-convert command")
    print("  - EPUB format will be merged into existing book records")
    print("  - This may take additional time depending on book count")
    print()
    
    while True:
        convert_choice = input("Convert imported eBooks to EPUB? (Y/N) [Y]: ").strip().upper()
        if convert_choice == '':
            convert_choice = 'Y'  # Default to Yes
        if convert_choice in ['Y', 'N']:
            break
        print_error("Please enter Y or N")
    
    config_progress['convert_to_epub'] = (convert_choice == 'Y')
    
    # Ask about skipping .kfx-zip files (only if conversion is enabled)
    kfx_zip_mode = 'convert_all'  # Default
    source_file_management = 'keep_both'  # Default
    
    if convert_choice == 'Y':
        # Clear screen and show progress before KFX-ZIP handling question
        os.system('cls')
        print()
        print_banner_and_version()
        print("=" * 70)
        print_step("PRE-FLIGHT CONFIGURATION WIZARD")
        print("=" * 70)
        print()
        print_ok(f"✓ [6/6] Calibre Auto-Import")
        print(f"  ✓ Library Path: {config_progress['library_path']}")
        convert_status = "Yes" if config_progress['convert_to_epub'] else "No"
        print(f"  ✓ Convert to EPUB: {convert_status}")
        print()
        
        print_step("KFX-ZIP File Handling")
        print("--------------------------------------------------")
        print()
        print("Files with .kfx-zip extension usually indicate DRM protection failure.")
        print("These files rarely convert successfully to EPUB.")
        print()
        print("Conversion modes:")
        print("  [A] Convert All - Attempt to convert all files including .kfx-zip (recommended)")
        print("  [S] Skip KFX-ZIP - Skip .kfx-zip files, convert regular .kfx files only")
        print()
        
        while True:
            mode_choice = input("Your choice (A/S) [A]: ").strip().upper()
            if mode_choice == '':
                mode_choice = 'A'  # Default to recommended option
            if mode_choice == 'A':
                kfx_zip_mode = 'convert_all'
                print()
                print_ok("Will attempt to convert all files including .kfx-zip")
                break
            elif mode_choice == 'S':
                kfx_zip_mode = 'skip_kfx_zip'
                print()
                print_ok("Will skip .kfx-zip files during conversion")
                break
            else:
                print_error("Invalid choice. Please enter A or S.")
        
        config_progress['kfx_zip_mode'] = kfx_zip_mode
        
        # Clear screen and show progress before source management question
        os.system('cls')
        print()
        print_banner_and_version()
        print("=" * 70)
        print_step("PRE-FLIGHT CONFIGURATION WIZARD")
        print("=" * 70)
        print()
        print_ok(f"✓ [6/6] Calibre Auto-Import")
        print(f"  ✓ Library Path: {config_progress['library_path']}")
        convert_status = "Yes" if config_progress['convert_to_epub'] else "No"
        print(f"  ✓ Convert to EPUB: {convert_status}")
        kfx_mode_display = "Convert All" if config_progress['kfx_zip_mode'] == 'convert_all' else "Skip KFX-ZIP"
        print(f"  ✓ KFX-ZIP Handling: {kfx_mode_display}")
        print()
        
        # Ask about source file management
        print_step("Source File Management")
        print("--------------------------------------------------")
        print()
        print("After successful EPUB conversion, what should happen to the source format files?")
        print()
        print("Options:")
        print("  [K] Keep Both - Preserve both source format and EPUB formats")
        print("  [D] Delete Source - Remove source format (KFX/AZW3/AZW) after successful EPUB conversion (recommended)")
        print("  [S] Smart Cleanup - Delete only .kfx-zip files, keep other formats")
        print()
        
        while True:
            choice = input("Your choice (K/D/S) [D]: ").strip().upper()
            if choice == '':
                choice = 'D'  # Default to recommended option
            if choice == 'K':
                print()
                print_ok("Will keep both source format and EPUB formats")
                source_file_management = 'keep_both'
                break
            elif choice == 'D':
                print()
                print_warn("Will delete source format after successful EPUB conversion")
                source_file_management = 'delete_source'
                break
            elif choice == 'S':
                print()
                print_ok("Will delete only .kfx-zip files, keeping other formats")
                source_file_management = 'delete_kfx_zip_only'
                break
            else:
                print_error("Invalid choice. Please enter K, D, or S.")
        
        print()
    
    # Build configuration
    config = {
        'enabled': True,
        'library_path': library_path,
        'convert_to_epub': convert_choice == 'Y',
        'kfx_zip_mode': kfx_zip_mode if convert_choice == 'Y' else 'convert_all',
        'source_file_management': source_file_management
    }
    
    return config

def cleanup_kfx_zip_books(library_path):
    """
    Query and optionally remove KFX-ZIP format books with user confirmation
    Returns: (removed_count, user_cancelled)
    """
    import sqlite3
    
    # Query for KFX-ZIP books with names
    db_path = os.path.join(library_path, "metadata.db")
    kfx_zip_books = []  # List of tuples: (book_id, book_name)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query: SELECT book, name FROM data WHERE format = 'KFX-ZIP'
        cursor.execute("SELECT book, name FROM data WHERE format = 'KFX-ZIP'")
        rows = cursor.fetchall()
        
        for row in rows:
            book_id = str(row[0])
            book_name = row[1]
            kfx_zip_books.append((book_id, book_name))
        
        conn.close()
        
    except Exception as e:
        print_error(f"Failed to query database: {e}")
        return 0, True
    
    if not kfx_zip_books:
        # No KFX-ZIP books found - silent success
        return 0, False
    
    # Show user-friendly list
    print()
    print_warn(f"Found {len(kfx_zip_books)} book(s) with KFX-ZIP format in database")
    print()
    print("These books may be DRM-protected versions that failed to decrypt.")
    print("Removing them allows clean import of newly decrypted versions.")
    print()
    print_warn("IMPORTANT: These KFX-ZIP books may NOT be related to current import!")
    print()
    print("Books to remove:")
    for book_id, book_name in kfx_zip_books:
        print(f"  [{book_id}] {book_name}")
    print()
    
    # User confirmation
    print("Options:")
    print("  [C] Continue - Remove these KFX-ZIP books and import (recommended)")
    print("  [S] Skip - Keep existing books, import with duplicates")
    print()
    
    while True:
        choice = input("Your choice (C/S) [C]: ").strip().upper()
        if choice == '':
            choice = 'C'  # Default to recommended option
        if choice == 'C':
            print()
            # Extract just the IDs for removal
            book_ids = [book_id for book_id, _ in kfx_zip_books]
            id_list = ','.join(book_ids)
            
            print_step(f"Removing {len(book_ids)} KFX-ZIP book(s)...")
            
            # Remove books using calibredb
            cmd = [
                'calibredb', 'remove',
                id_list,
                '--permanent',
                f'--library-path={library_path}'
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    print_ok(f"Successfully removed {len(book_ids)} book(s)")
                    print()
                    return len(book_ids), False
                else:
                    print_error(f"Failed to remove books: {result.stderr}")
                    print()
                    return 0, True
                    
            except Exception as e:
                print_error(f"Failed to remove books: {e}")
                print()
                return 0, True
                
        elif choice == 'S':
            print()
            print_warn("Skipping KFX-ZIP cleanup - will use duplicates mode")
            print()
            return 0, True
        else:
            print_error("Invalid choice. Please enter C or S.")

def find_all_azw_files(content_dir, exclude_asins=None):
    """
    Recursively find all .azw files in content directory
    Optionally exclude files matching ASINs that failed key extraction
    Returns: list of full file paths
    """
    azw_files = []
    exclude_asins = exclude_asins or []
    
    try:
        for root, dirs, files in os.walk(content_dir):
            for file in files:
                if file.lower().endswith('.azw'):
                    # Extract ASIN from filename (e.g., B00N17VVZC_EBOK.azw)
                    asin = file.split('_')[0] if '_' in file else file.replace('.azw', '')
                    
                    # Skip if this ASIN failed key extraction
                    if asin in exclude_asins:
                        continue
                    
                    full_path = os.path.join(root, file)
                    azw_files.append(full_path)
        
        return azw_files
        
    except Exception as e:
        print_error(f"Error scanning directory: {e}")
        return []

def import_single_book(book_path, library_path, use_duplicates=False, timeout_seconds=60):
    """
    Import a single book to Calibre with timeout
    Returns: (success: bool, book_id: str or None, error_msg: str or None, timed_out: bool, already_exists: bool, book_title: str or None)
    """
    cmd = ['calibredb', 'add']
    
    if use_duplicates:
        cmd.append('-d')
    
    cmd.extend([
        '-1',  # One book per directory
        book_path,
        f'--library-path={library_path}'
    ])
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            encoding='utf-8',
            errors='replace'
        )
        
        # Parse output for book ID
        if result.returncode == 0 and result.stdout:
            # Look for "Added book ids: 123"
            for line in result.stdout.split('\n'):
                if 'Added book ids:' in line:
                    ids_str = line.split('Added book ids:')[1].strip()
                    book_id = ids_str.split(',')[0].strip() if ids_str else None
                    return True, book_id, None, False, False, None
        
        # Check if book already exists in database
        error_msg = result.stderr if result.stderr else "Unknown error"
        already_exists = False
        book_title = None
        
        if "already exist in the database" in error_msg:
            already_exists = True
            # Extract book title from error message
            # Format: "The following books were not added as they already exist in the database:\n  Book Title"
            lines = error_msg.split('\n')
            for i, line in enumerate(lines):
                if "already exist in the database" in line:
                    # Next non-empty line should contain the book title
                    for j in range(i + 1, len(lines)):
                        title_line = lines[j].strip()
                        if title_line and not title_line.startswith('('):
                            book_title = title_line
                            break
                    break
        
        return False, None, error_msg, False, already_exists, book_title
        
    except subprocess.TimeoutExpired:
        # Kill the process
        return False, None, f"Timeout after {timeout_seconds} seconds", True, False, None
        
    except Exception as e:
        return False, None, str(e), False, False, None

def write_import_log(library_path, results, azw_files, script_dir):
    """
    Write detailed import log to file
    Returns: log file path
    """
    # Create logs directory with import subfolder
    logs_dir = os.path.join(script_dir, "Logs", "import_logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"calibre_import_{timestamp}.log")
    
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 70 + "\n")
            f.write("CALIBRE IMPORT LOG\n")
            f.write("=" * 70 + "\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Library: {library_path}\n")
            f.write(f"Total Books Found: {len(azw_files)}\n")
            f.write(f"Timeout per book: 60 seconds\n")
            f.write("\n")
            
            # Failed imports section
            if results['failed'] > 0:
                f.write("-" * 70 + "\n")
                f.write(f"FAILED IMPORTS ({results['failed']})\n")
                f.write("-" * 70 + "\n")
                for book_name, error_msg in results['failed_books']:
                    f.write(f"\n[FAILED] {book_name}\n")
                    f.write(f"  Error: {error_msg if error_msg else 'Unknown error'}\n")
                f.write("\n")
            
            # Timeout section
            if results['timed_out'] > 0:
                f.write("-" * 70 + "\n")
                f.write(f"TIMEOUT IMPORTS ({results['timed_out']})\n")
                f.write("-" * 70 + "\n")
                for book_name in results['timed_out_books']:
                    f.write(f"\n[TIMEOUT] {book_name}\n")
                    f.write(f"  Duration: Exceeded 60 seconds\n")
                    f.write(f"  Note: Book may be stuck in DeDRM processing\n")
                f.write("\n")
            
            # Success section (summary only)
            if results['success'] > 0:
                f.write("-" * 70 + "\n")
                f.write(f"SUCCESSFUL IMPORTS ({results['success']})\n")
                f.write("-" * 70 + "\n")
                f.write(f"Book IDs: {', '.join(results['book_ids'])}\n")
                f.write("\n")
            
            # Summary
            f.write("=" * 70 + "\n")
            f.write("SUMMARY\n")
            f.write("=" * 70 + "\n")
            f.write(f"Total:    {results['total']}\n")
            f.write(f"Success:  {results['success']}\n")
            f.write(f"Failed:   {results['failed']}\n")
            f.write(f"Timeout:  {results['timed_out']}\n")
            f.write("=" * 70 + "\n")
        
        return log_file
        
    except Exception as e:
        print_warn(f"Failed to write log file: {e}")
        return None

def import_all_azw_files(content_dir, library_path, use_duplicates=False, per_book_timeout=60, exclude_asins=None):
    """
    Import all *.azw files one at a time with individual timeouts
    Optionally exclude ASINs that failed key extraction
    Returns: dict with detailed results
    """
    print_step("Importing ebooks to Calibre...")
    print("--------------------------------------------------")
    print()
    
    # Find all .azw files (excluding failed ASINs)
    print_step("Scanning for .azw files...")
    azw_files = find_all_azw_files(content_dir, exclude_asins=exclude_asins)
    
    if not azw_files:
        print_warn("No .azw files found")
        print()
        return {
            'total': 0,
            'success': 0,
            'failed': 0,
            'timed_out': 0,
            'book_ids': [],
            'failed_books': [],
            'timed_out_books': [],
            'log_file': None
        }
    
    print_ok(f"Found {len(azw_files)} .azw file(s)")
    print()
    
    # Import each book individually
    results = {
        'total': len(azw_files),
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'timed_out': 0,
        'book_ids': [],
        'failed_books': [],
        'skipped_books': [],
        'timed_out_books': [],
        'log_file': None
    }
    
    print_step(f"Importing books (timeout: {per_book_timeout}s per book)...")
    print()
    
    for idx, book_path in enumerate(azw_files, 1):
        book_name = os.path.basename(book_path)
        # Extract ASIN from filename (e.g., B00JBVUJM8_EBOK.azw -> B00JBVUJM8_EBOK)
        asin = os.path.splitext(book_name)[0]
        
        print(f"[{idx}/{len(azw_files)}] {book_name}...", end=' ', flush=True)
        
        success, book_id, error_msg, timed_out, already_exists, book_title = import_single_book(
            book_path, 
            library_path, 
            use_duplicates, 
            per_book_timeout
        )
        
        if success and book_id:
            print_ok(f"✓ (ID: {book_id})")
            results['success'] += 1
            results['book_ids'].append(book_id)
        elif timed_out:
            print_error(f"⏱ TIMEOUT")
            results['timed_out'] += 1
            results['timed_out_books'].append(book_name)
        elif already_exists:
            print_colored(f"[SKIPPED] ✗ Book already exists in the database", 'yellow')
            results['skipped'] += 1
            results['skipped_books'].append((asin, book_title if book_title else "Unknown Title"))
        else:
            print_error(f"✗ FAILED")
            results['failed'] += 1
            results['failed_books'].append((book_name, error_msg))
    
    print()
    
    # Write log file if there were any failures or timeouts
    if results['failed'] > 0 or results['timed_out'] > 0:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_file = write_import_log(library_path, results, azw_files, script_dir)
        results['log_file'] = log_file
    
    return results

def display_import_results(results):
    """
    Display import results to user
    Handles both old format (subprocess result) and new format (dict)
    """
    print("--------------------------------------------------")
    print_step("Import Results:")
    print()
    
    if not results:
        print_error("Import failed - no results")
        return
    
    # Check if it's the new dict format or old subprocess result
    if isinstance(results, dict):
        # New format from per-book import
        if results['success'] > 0:
            print_ok(f"Successfully imported: {results['success']} ebook(s)")
            if results['book_ids']:
                print(f"      Book IDs: {', '.join(results['book_ids'])}")
        else:
            print_warn("No books were imported")
        
        # Show skipped books (duplicates)
        if results.get('skipped', 0) > 0:
            print()
            print_warn(f"Skipped: {results['skipped']} book(s) already exist in database")
            if results.get('skipped_books'):
                print("      Books that were skipped:")
                for asin, title in results['skipped_books'][:5]:  # Show first 5
                    print(f"        - {asin} - {title}")
                if len(results['skipped_books']) > 5:
                    print(f"        ... and {len(results['skipped_books']) - 5} more")
        
        # Show timeout information
        if results.get('timed_out', 0) > 0:
            print()
            print_error(f"Timed out: {results['timed_out']} book(s)")
            if results.get('timed_out_books'):
                print("      Books that timed out:")
                for book_name in results['timed_out_books'][:5]:  # Show first 5
                    print(f"        - {book_name}")
                if len(results['timed_out_books']) > 5:
                    print(f"        ... and {len(results['timed_out_books']) - 5} more")
        
        # Show failed books
        if results.get('failed', 0) > 0:
            print()
            print_error(f"Failed: {results['failed']} book(s)")
            if results.get('failed_books'):
                print("      Books that failed:")
                for book_name, error in results['failed_books'][:3]:  # Show first 3
                    print(f"        - {book_name}")
                if len(results['failed_books']) > 3:
                    print(f"        ... and {len(results['failed_books']) - 3} more")
        
        # Show log file location if it exists
        if results.get('log_file'):
            print()
            print_step(f"Detailed error log saved to:")
            print(f"      {results['log_file']}")
    
    print()

def is_calibre_running():
    """
    Check if any Calibre processes are currently running on Windows
    Returns: True if Calibre is running, False otherwise
    """
    try:
        # Run tasklist command to get all running processes
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq calibre*'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Check for common Calibre process names
        calibre_processes = [
            'calibre.exe',
            'calibre-parallel.exe',
            'calibredb.exe',
            'ebook-convert.exe'
        ]
        
        output_lower = result.stdout.lower()
        for process in calibre_processes:
            if process.lower() in output_lower:
                return True
        
        return False
        
    except Exception as e:
        # If detection fails, assume Calibre might be running (safer approach)
        print_warn(f"Could not detect Calibre processes: {e}")
        return True

def verify_calibre_closed_with_loop():
    """
    Verify Calibre is closed with retry loop
    Returns: True if Calibre is closed, False if user wants to exit
    """
    while True:
        if not is_calibre_running():
            print_ok("Calibre confirmed closed - proceeding")
            print()
            return True
        
        # Calibre is still running
        print_warn("Calibre is still running!")
        print()
        print("Options:")
        print("  [R] Retry - Check again after closing Calibre")
        print("  [Q] Quit - Exit script")
        print()
        
        while True:
            choice = input("Your choice (R/Q) [R]: ").strip().upper()
            if choice == '':
                choice = 'R'  # Default to Retry
            if choice in ['R', 'Q']:
                break
            print_error("Invalid choice. Please enter R or Q.")
        
        if choice == 'R':
            print()
            print_step("Checking again...")
            continue  # Loop back to check again
        elif choice == 'Q':
            print()
            print_warn("Script cancelled by user")
            return False

def warn_close_calibre():
    """
    Warn user to close Calibre before import
    Auto-detects if Calibre is running and skips prompt if not
    Returns: True if user confirms or Calibre not running, False otherwise
    """
    # Check if Calibre is running
    if not is_calibre_running():
        print_ok("Calibre not detected - proceeding automatically")
        print()
        return True
    
    print_warn("IMPORTANT: Calibre must be closed for import to work!")
    print()
    print("Please close Calibre now if it's running.")
    print("Importing while Calibre is open may cause:")
    print("  - Database lock errors")
    print("  - Import failures")
    print("  - Data corruption")
    print()
    print_warn("BE AWARE:")
    print("This will attempt to Import ALL BOOKS found ")
    print("in your 'My Kindle Content' location and with any luck they")
    print("should be DeDRM and end up in 'KFX' & 'EPUB' format (If you selected to convert to EPUB)")
    print("-- Good Luck --")
    print()
    
    input("Press Enter once Calibre is closed to continue...")
    print()
    
    # VERIFY closure with retry loop
    return verify_calibre_closed_with_loop()

# ============================================================================
# KFX TO EPUB CONVERSION FUNCTIONS
# ============================================================================

def query_book_info_from_db(library_path, book_ids):
    """
    Query Calibre database for book titles, authors, and paths
    Returns: dict mapping book_id -> {'title': str, 'author': str, 'path': str}
    """
    import sqlite3
    
    db_path = os.path.join(library_path, "metadata.db")
    book_info = {}
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for book_id in book_ids:
            # Get title and path
            cursor.execute("SELECT title, path FROM books WHERE id = ?", (book_id,))
            result = cursor.fetchone()
            
            if result:
                title = result[0]
                path = result[1]
                
                # Get author
                cursor.execute("""
                    SELECT authors.name 
                    FROM authors 
                    JOIN books_authors_link ON authors.id = books_authors_link.author
                    WHERE books_authors_link.book = ?
                    LIMIT 1
                """, (book_id,))
                author_result = cursor.fetchone()
                author = author_result[0] if author_result else "Unknown Author"
                
                book_info[book_id] = {
                    'title': title,
                    'author': author,
                    'path': path
                }
        
        conn.close()
        return book_info
        
    except Exception as e:
        print_error(f"Failed to query database: {e}")
        return {}

def query_book_paths_from_db(library_path, book_ids):
    """
    Query Calibre metadata.db to get book paths for given book IDs
    Returns: dict mapping book_id -> book_path
    (Legacy function - use query_book_info_from_db for enhanced info)
    """
    book_info = query_book_info_from_db(library_path, book_ids)
    return {book_id: info['path'] for book_id, info in book_info.items()}

def find_source_file_in_directory(book_dir):
    """
    Find the source ebook file in the book directory.
    Searches for Kindle format files: .kfx, .azw, .azw3, or .kfx-zip
    
    Args:
        book_dir: Path to the book directory in Calibre library
    
    Returns:
        tuple: (filename, is_kfx_zip) or (None, False) if not found
               - filename: Name of the source file found
               - is_kfx_zip: True if file is .kfx-zip format, False otherwise
    """
    try:
        if not os.path.exists(book_dir):
            return None, False
        
        for filename in os.listdir(book_dir):
            lower_name = filename.lower()
            if lower_name.endswith(('.kfx', '.azw', '.azw3', '.kfx-zip')):
                is_kfx_zip = lower_name.endswith('.kfx-zip')
                return filename, is_kfx_zip
        
        return None, False
        
    except Exception as e:
        print_error(f"Error searching directory {book_dir}: {e}")
        return None, False

def convert_book_to_epub(source_path, epub_path):
    """
    Convert Imported eBook to EPUB using ebook-convert
    Returns: (success: bool, error_message: str)
    """
    try:
        cmd = [
            'ebook-convert',
            source_path,
            epub_path,
            '--input-profile=default',
            '--output-profile=tablet',
            '--no-svg-cover',
            '--epub-version=3'
        ]
        
        # Use UTF-8 encoding with error handling to prevent Windows cp1252 decode errors
        result = subprocess.run(cmd, capture_output=True, text=True, 
                               encoding='utf-8', errors='replace', timeout=300)
        
        if result.returncode == 0 and os.path.exists(epub_path):
            return True, ""
        else:
            error_msg = result.stderr if result.stderr else "Conversion failed"
            return False, error_msg
            
    except subprocess.TimeoutExpired:
        return False, "Conversion timeout (5 minutes)"
    except Exception as e:
        return False, str(e)

def convert_azw3_via_mobi(source_path, epub_path):
    """
    Convert AZW3 to EPUB via temporary MOBI intermediate format
    Two-step conversion: AZW3 → MOBI → EPUB
    
    This produces better results than direct AZW3 → EPUB conversion
    because MOBI acts as a better intermediate format for preserving
    layout and formatting.
    
    Temp MOBI file is created in temp_extraction folder for automatic
    cleanup by cleanup_temp_extraction() on next script run.
    
    Args:
        source_path: Path to source AZW3 file
        epub_path: Path to output EPUB file
    
    Returns:
        tuple: (success: bool, error_message: str)
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    temp_extraction_dir = os.path.join(script_dir, "temp_extraction")
    
    # Fixed filename - safe because conversions happen sequentially
    temp_mobi_path = os.path.join(temp_extraction_dir, "temp_conversion.mobi")
    
    try:
        # Ensure temp directory exists
        os.makedirs(temp_extraction_dir, exist_ok=True)
        
        # Step 1: Convert AZW3 to MOBI
        cmd_mobi = [
            'ebook-convert',
            source_path,
            temp_mobi_path,
            '--input-profile=default',
            '--output-profile=tablet'
        ]
        
        result_mobi = subprocess.run(
            cmd_mobi,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=300
        )
        
        if result_mobi.returncode != 0 or not os.path.exists(temp_mobi_path):
            error_msg = result_mobi.stderr if result_mobi.stderr else "AZW3 to MOBI conversion failed"
            return False, f"Step 1 failed: {error_msg}"
        
        # Step 2: Convert MOBI to EPUB
        cmd_epub = [
            'ebook-convert',
            temp_mobi_path,
            epub_path,
            '--input-profile=default',
            '--output-profile=tablet',
            '--no-svg-cover',
            '--epub-version=3'
        ]
        
        result_epub = subprocess.run(
            cmd_epub,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=300
        )
        
        if result_epub.returncode == 0 and os.path.exists(epub_path):
            return True, ""
        else:
            error_msg = result_epub.stderr if result_epub.stderr else "MOBI to EPUB conversion failed"
            return False, f"Step 2 failed: {error_msg}"
            
    except subprocess.TimeoutExpired:
        return False, "Conversion timeout (5 minutes per step)"
    except Exception as e:
        return False, str(e)
    finally:
        # Always try to cleanup temp MOBI file
        if os.path.exists(temp_mobi_path):
            try:
                os.remove(temp_mobi_path)
            except Exception:
                pass  # If cleanup fails, cleanup_temp_extraction() will handle it on next run

def add_epub_format_to_calibre(book_id, epub_path, library_path):
    """
    Add EPUB format to existing Calibre book record using calibredb add_format
    Returns: (success: bool, error_message: str)
    """
    try:
        cmd = [
            'calibredb', 'add_format',
            str(book_id),
            epub_path,
            f'--library-path={library_path}'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            return True, ""
        else:
            error_msg = result.stderr if result.stderr else "Failed to add format"
            return False, error_msg
            
    except subprocess.TimeoutExpired:
        return False, "Add format timeout"
    except Exception as e:
        return False, str(e)

def prompt_source_file_management():
    """
    Ask user what to do with source KFX files after successful EPUB conversion
    Returns: 'keep_both' | 'delete_kfx' | 'delete_kfx_zip_only'
    """
    print_step("Source File Management")
    print("--------------------------------------------------")
    print()
    print("After successful EPUB conversion, what should happen to the source KFX files?")
    print()
    print("Options:")
    print("  [K] Keep Both - Preserve both KFX and EPUB formats (recommended)")
    print("  [D] Delete KFX - Remove KFX format after successful EPUB conversion")
    print("  [S] Smart Cleanup - Delete only .kfx-zip files, keep regular .kfx files")
    print()
    
    while True:
        choice = input("Your choice (K/D/S): ").strip().upper()
        if choice == 'K':
            print()
            print_ok("Will keep both KFX and EPUB formats")
            print()
            return 'keep_both'
        elif choice == 'D':
            print()
            print_warn("Will delete KFX format after successful EPUB conversion")
            print()
            return 'delete_kfx'
        elif choice == 'S':
            print()
            print_ok("Will delete only .kfx-zip files, keeping regular .kfx files")
            print()
            return 'delete_kfx_zip_only'
        else:
            print_error("Invalid choice. Please enter K, D, or S.")

def remove_format_from_calibre(book_id, format_name, library_path):
    """
    Remove a specific format from Calibre book record using calibredb
    Returns: (success: bool, error_message: str)
    """
    try:
        cmd = [
            'calibredb', 'remove_format',
            str(book_id),
            format_name.upper(),
            f'--library-path={library_path}'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            return True, ""
        else:
            error_msg = result.stderr if result.stderr else "Failed to remove format"
            return False, error_msg
            
    except subprocess.TimeoutExpired:
        return False, "Remove format timeout"
    except Exception as e:
        return False, str(e)

def write_conversion_log(library_path, stats, book_info, script_dir):
    """
    Write detailed conversion log to file
    Returns: log file path
    """
    # Create logs directory with conversion subfolder
    logs_dir = os.path.join(script_dir, "Logs", "conversion_logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"calibre_conversion_{timestamp}.log")
    
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 70 + "\n")
            f.write("CALIBRE KFX TO EPUB CONVERSION LOG\n")
            f.write("=" * 70 + "\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Library: {library_path}\n")
            f.write(f"Total Books Processed: {stats['total']}\n")
            f.write(f"Timeout per book: 300 seconds (5 minutes)\n")
            f.write("\n")
            
            # Failed conversions section
            if stats.get('failed_conversions'):
                f.write("-" * 70 + "\n")
                f.write(f"FAILED CONVERSIONS ({len(stats['failed_conversions'])})\n")
                f.write("-" * 70 + "\n")
                for book_id, title, author, error_msg in stats['failed_conversions']:
                    f.write(f"\n[FAILED] {title}\n")
                    f.write(f"  Author: {author}\n")
                    f.write(f"  Book ID: {book_id}\n")
                    f.write(f"  Error: {error_msg}\n")
                f.write("\n")
            
            # Failed merges section
            if stats.get('failed_merges'):
                f.write("-" * 70 + "\n")
                f.write(f"FAILED MERGES TO CALIBRE ({len(stats['failed_merges'])})\n")
                f.write("-" * 70 + "\n")
                for book_id, title, author, error_msg in stats['failed_merges']:
                    f.write(f"\n[FAILED MERGE] {title}\n")
                    f.write(f"  Author: {author}\n")
                    f.write(f"  Book ID: {book_id}\n")
                    f.write(f"  Error: {error_msg}\n")
                f.write("\n")
            
            # Skipped books section
            if stats.get('skipped_books'):
                f.write("-" * 70 + "\n")
                f.write(f"SKIPPED BOOKS ({len(stats['skipped_books'])})\n")
                f.write("-" * 70 + "\n")
                for book_id, title, author, reason in stats['skipped_books']:
                    f.write(f"\n[SKIPPED] {title}\n")
                    f.write(f"  Author: {author}\n")
                    f.write(f"  Book ID: {book_id}\n")
                    f.write(f"  Reason: {reason}\n")
                f.write("\n")
            
            # Success section (summary only)
            if stats['converted'] > 0:
                f.write("-" * 70 + "\n")
                f.write(f"SUCCESSFUL CONVERSIONS ({stats['converted']})\n")
                f.write("-" * 70 + "\n")
                f.write(f"Books successfully converted and merged to EPUB format\n")
                f.write("\n")
            
            # Summary
            f.write("=" * 70 + "\n")
            f.write("SUMMARY\n")
            f.write("=" * 70 + "\n")
            f.write(f"Total:              {stats['total']}\n")
            f.write(f"Converted:          {stats['converted']}\n")
            f.write(f"Merged to Calibre:  {stats['merged']}\n")
            f.write(f"Failed:             {stats['failed']}\n")
            f.write(f"Skipped:            {stats.get('skipped_kfx_zip', 0)}\n")
            if stats.get('source_files_deleted', 0) > 0:
                f.write(f"Source Files Deleted: {stats['source_files_deleted']}\n")
            f.write("=" * 70 + "\n")
        
        return log_file
        
    except Exception as e:
        print_warn(f"Failed to write conversion log file: {e}")
        return None

def process_book_conversions(library_path, book_ids, calibre_config=None):
    """
    Main orchestrator for Phase 4: KFX to EPUB conversion
    Returns: dict with conversion statistics
    """
    # Load config to check clear screen setting
    config = load_config()
    if config and config.get('clear_screen_between_phases', True):
        os.system('cls')
    
    display_phase_banner(4, "Imported eBook to EPUB Conversion")
    
    stats = {
        'total': len(book_ids),
        'converted': 0,
        'merged': 0,
        'failed': 0,
        'errors': [],
        'source_files_deleted': 0,
        'failed_conversions': [],
        'failed_merges': [],
        'skipped_books': []
    }
    
    if not book_ids:
        print_warn("No books to convert")
        return stats
    
    # Use passed config or load from unified config
    if calibre_config is None:
        unified_config = load_config()
        calibre_config = unified_config.get('calibre_import', {}) if unified_config else {}
    
    # Get settings from config
    kfx_zip_mode = calibre_config.get('kfx_zip_mode', 'convert_all')
    skip_kfx_zip = (kfx_zip_mode == 'skip_kfx_zip')
    source_management = calibre_config.get('source_file_management', 'keep_both')
    
    print_step(f"Converting {len(book_ids)} book(s) to EPUB format...")
    print()
    
    # Query database for book info (titles, authors, paths)
    print_step("Querying Calibre database for book information...")
    book_info = query_book_info_from_db(library_path, book_ids)
    
    if not book_info:
        print_error("Failed to retrieve book information from database")
        return stats
    
    print_ok(f"Retrieved information for {len(book_info)} book(s)")
    print()
    
    # Add tracking for skipped and DRM-protected files
    stats['skipped_kfx_zip'] = 0
    stats['failed_drm_protected'] = 0
    
    # Process each book
    for idx, (book_id, info) in enumerate(book_info.items(), 1):
        title = info['title']
        author = info['author']
        book_path = info['path']
        
        print_step(f"Processing book {idx}/{len(book_info)}: '{title}' by {author}")
        
        # Construct full path to book directory
        book_dir = os.path.join(library_path, book_path)
        
        # Find source file (returns tuple: filename, is_kfx_zip)
        source_filename, is_kfx_zip = find_source_file_in_directory(book_dir)
        
        if not source_filename:
            error_msg = f"No source file (KFX/AZW/AZW3/KFX-ZIP) found in {book_path}"
            print_error(error_msg)
            stats['failed'] += 1
            stats['errors'].append(f"Book {book_id}: {error_msg}")
            stats['failed_conversions'].append((book_id, title, author, error_msg))
            print()
            continue
        
        # Check if we should skip .kfx-zip files
        if is_kfx_zip and skip_kfx_zip:
            print(f"  Source: {source_filename}")
            print(f"  Skipping .kfx-zip file (DRM-protected)")
            stats['skipped_kfx_zip'] += 1
            stats['skipped_books'].append((book_id, title, author, "KFX-ZIP file (DRM-protected)"))
            print()
            continue
        
        source_path = os.path.join(book_dir, source_filename)
        epub_filename = os.path.splitext(source_filename)[0] + '.epub'
        epub_path = os.path.join(book_dir, epub_filename)
        
        print(f"  Source: {source_filename}")
        print(f"  Target: {epub_filename}")
        
        # Detect if this is AZW3 format
        is_azw3 = source_filename.lower().endswith('.azw3')
        
        # Convert to EPUB (route based on format)
        if is_azw3:
            print("  Converting to EPUB (via MOBI intermediate)...")
            success, error = convert_azw3_via_mobi(source_path, epub_path)
        else:
            print("  Converting to EPUB...")
            success, error = convert_book_to_epub(source_path, epub_path)
        
        if not success:
            print_error(f"  {error}")
            stats['failed'] += 1
            # Track if it's likely a DRM-protected file
            if is_kfx_zip:
                stats['failed_drm_protected'] += 1
            stats['errors'].append(f"Book {book_id}: Conversion failed - {error}")
            stats['failed_conversions'].append((book_id, title, author, error))
            print()
            continue
        
        print_ok("  Conversion successful")
        stats['converted'] += 1
        
        # Merge EPUB format into Calibre
        print("  Merging EPUB format to Calibre...")
        success, error = add_epub_format_to_calibre(book_id, epub_path, library_path)
        
        if not success:
            print_error(f"  {error}")
            stats['errors'].append(f"Book {book_id}: Failed to merge format - {error}")
            stats['failed_merges'].append((book_id, title, author, error))
        else:
            print_ok("  EPUB format merged successfully")
            stats['merged'] += 1
            
            # Handle source file management based on user choice
            if source_management == 'delete_source':
                # Determine the actual source format to delete
                source_ext = os.path.splitext(source_filename)[1].upper().replace('.', '')
                
                # Delete the actual source format (KFX, AZW3, AZW, or KFX-ZIP)
                print(f"  Removing {source_ext} format from Calibre...")
                success, error = remove_format_from_calibre(book_id, source_ext, library_path)
                if success:
                    print_ok(f"  {source_ext} format removed")
                    stats['source_files_deleted'] += 1
                else:
                    print_warn(f"  Failed to remove {source_ext} format: {error}")
            
            elif source_management == 'delete_kfx_zip_only' and is_kfx_zip:
                # Delete only .kfx-zip files
                print("  Removing KFX-ZIP format from Calibre...")
                success, error = remove_format_from_calibre(book_id, 'KFX-ZIP', library_path)
                if success:
                    print_ok("  KFX-ZIP format removed")
                    stats['source_files_deleted'] += 1
                else:
                    print_warn(f"  Failed to remove KFX-ZIP format: {error}")
        
        print()
    
    # Display summary
    print("--------------------------------------------------")
    print_step("Conversion Summary:")
    print()
    print_ok(f"Total books processed: {stats['total']}")
    print_ok(f"Successfully converted: {stats['converted']}")
    print_ok(f"Successfully merged to Calibre: {stats['merged']}")
    
    if stats['failed'] > 0:
        print_error(f"Failed conversions: {stats['failed']}")
        if stats['failed_drm_protected'] > 0:
            print_error(f"  Failed (likely DRM-protected): {stats['failed_drm_protected']}")
    
    if stats['skipped_kfx_zip'] > 0:
        print_warn(f"Skipped (.kfx-zip files): {stats['skipped_kfx_zip']}")
    
    if stats['source_files_deleted'] > 0:
        print_ok(f"Source files removed: {stats['source_files_deleted']}")
    
    # Write log file if there were any failures or skipped books
    if stats['failed'] > 0 or stats.get('skipped_kfx_zip', 0) > 0 or stats.get('failed_merges'):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_file = write_conversion_log(library_path, stats, book_info, script_dir)
        if log_file:
            print()
            print_step(f"Detailed conversion log saved to:")
            print(f"      {log_file}")
    
    # Display Phase 4 summary
    summary_points = [
        f"Processed {stats['total']} book(s) for EPUB conversion",
        f"Successfully converted: {stats['converted']} book(s)",
        f"Successfully merged to Calibre: {stats['merged']} book(s)"
    ]
    
    if stats['failed'] > 0:
        summary_points.append(f"Failed conversions: {stats['failed']} book(s)")
    
    if stats['skipped_kfx_zip'] > 0:
        summary_points.append(f"Skipped .kfx-zip files: {stats['skipped_kfx_zip']}")
    
    if stats['source_files_deleted'] > 0:
        summary_points.append(f"Source files removed: {stats['source_files_deleted']}")
    
    display_phase_summary(4, "KFX to EPUB Conversion", summary_points, pause_seconds=5)
    
    # Cleanup temp_extraction folder after all conversions complete
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cleanup_temp_extraction(silent=True)
    
    return stats

def attempt_calibre_import(content_dir, script_dir, calibre_already_confirmed=False, extraction_stats=None):
    """
    Main entry point for Calibre auto-import functionality
    Simplified approach using direct library path
    Returns: tuple (imported_count, book_ids, config) for Phase 4 processing
    
    Args:
        calibre_already_confirmed: If True, skip asking user to close Calibre (already asked in pre-flight)
        extraction_stats: Dict with extraction statistics including failed_books list
    """
    # Load config to check clear screen setting
    config = load_config()
    if config and config.get('clear_screen_between_phases', True):
        os.system('cls')
    
    display_phase_banner(3, "Calibre Auto-Import")
    
    try:
        # Load unified config to get calibre_import settings
        unified_config = load_config()
        
        if not unified_config or 'calibre_import' not in unified_config:
            print_warn("Calibre auto-import not configured")
            print()
            return 0
        
        config = unified_config['calibre_import']
        
        # Check if Calibre import is enabled
        if not config.get('enabled', False):
            print_warn("Calibre auto-import is disabled in configuration")
            print()
            return 0
        
        print_step("Configuration validated successfully!")
        
        # Get book count for display
        book_count = get_library_book_count(config['library_path'])
        if book_count is not None:
            print(f"Library path: {config['library_path']} ({book_count} books)")
        else:
            print(f"Library path: {config['library_path']}")
        print()
        
        # Only ask to close Calibre if not already confirmed
        if not calibre_already_confirmed:
            if not warn_close_calibre():
                print_warn("Import cancelled by user")
                print()
                return 0
        
        # Extract list of failed ASINs from extraction stats
        exclude_asins = []
        if extraction_stats and extraction_stats.get('failed_books'):
            exclude_asins = [asin for asin, _, _ in extraction_stats['failed_books']]
            if exclude_asins:
                print_warn(f"Excluding {len(exclude_asins)} book(s) that failed key extraction from import")
                print()
        
        # Phase 3a: Optional cleanup of KFX-ZIP books
        print_step("[PHASE 3a] Checking for existing KFX-ZIP books...")
        removed_count, cleanup_skipped = cleanup_kfx_zip_books(config['library_path'])
        
        # Import all ebooks (use duplicates flag if cleanup was skipped)
        # Pass exclude_asins to skip books that failed key extraction
        # Returns dict with: total, success, failed, timed_out, book_ids, failed_books, timed_out_books
        results = import_all_azw_files(content_dir, config['library_path'], use_duplicates=cleanup_skipped, exclude_asins=exclude_asins)
        
        # Extract stats from results dict
        imported_count = results['success']
        book_ids = results['book_ids']
        
        # Display results
        display_import_results(results)
        
        # Build summary points
        summary_points = [
            f"Imported {imported_count} ebook(s) to Calibre library",
            f"Books added with IDs: {', '.join(book_ids) if book_ids else 'None'}",
            "DeDRM plugin automatically processed all imports",
            "Books are now available in Calibre"
        ]
        
        # Add timeout/failure info to summary if applicable
        if results.get('timed_out', 0) > 0:
            summary_points.append(f"Timed out: {results['timed_out']} book(s) - continuing with remaining books")
        
        if results.get('failed', 0) > 0:
            summary_points.append(f"Failed: {results['failed']} book(s) - check error messages above")
        
        display_phase_summary(3, "Calibre Auto-Import", summary_points, pause_seconds=5)
        
        # Return tuple: (imported_count, book_ids, config, results)
        return (imported_count, book_ids, config, results)
        
    except KeyboardInterrupt:
        print()
        print_warn("Calibre auto-import cancelled by user")
        print()
        return 0
    except Exception as e:
        print_error(f"Calibre auto-import failed: {e}")
        print()
        return 0

def main():
    # === OS CHECK: Windows Only ===
    current_os = platform.system()
    
    if current_os != 'Windows':
        os.system('clear' if current_os != 'Windows' else 'cls')
        print()
        print_error("=" * 70)
        print_error("THIS SCRIPT ONLY WORKS ON WINDOWS!")
        print_error("=" * 70)
        print()
        print_error(f"Current OS detected: {current_os}")
        print()
        print("This script is designed for Windows 11 and relies on Windows-specific:")
        print("  - File paths (C:\\Users\\...\\AppData\\...)")
        print("  - Kindle for PC installation locations")
        print("  - Calibre configuration file locations (AppData\\Roaming\\calibre)")
        print()
        print("=" * 70)
        print_step("MANUAL EXTRACTION INSTRUCTIONS")
        print("=" * 70)
        print()
        print("To manually extract Kindle keys, run Satsuoni's KFXKeyExtractor28.exe:")
        print()
        print("  KFXKeyExtractor28.exe <content_dir> <output_key> <output_k4i>")
        print()
        print("Example:")
        print('  KFXKeyExtractor28.exe "C:\\Users\\YourName\\Documents\\My Kindle Content" "kindlekey.txt" "kindlekey.k4i"')
        print()
        print("Where:")
        print("  <content_dir>  = Path to your Kindle content folder")
        print("  <output_key>   = Output file for key (e.g., kindlekey.txt)")
        print("  <output_k4i>   = Output file for account data (e.g., kindlekey.k4i)")
        print()
        print("=" * 70)
        print_step("NEED HELP ON NON-WINDOWS SYSTEMS?")
        print("=" * 70)
        print()
        print("For assistance running this on Mac/Linux or other non-Windows systems,")
        print("please visit Satsuoni's GitHub Repository and request help from the")
        print("author directly:")
        print()
        print_colored("  https://github.com/Satsuoni/DeDRM_tools/discussions", 'cyan')
        print()
        print("=" * 70)
        print()
        input("Press Enter to exit...")
        return 1
    
    # Define paths - use script directory and current user instead of hardcoded paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    fixed_dir = script_dir
    user_home = os.path.expanduser("~")
    extractor = os.path.join(fixed_dir, "KFXKeyExtractor28.exe")
    
    # Create Keys folder for key files
    keys_dir = os.path.join(fixed_dir, "Keys")
    os.makedirs(keys_dir, exist_ok=True)
    output_key = os.path.join(keys_dir, "kindlekey.txt")
    output_k4i = os.path.join(keys_dir, "kindlekey.k4i")
    
    dedrm_json = os.path.join(user_home, "AppData", "Roaming", "calibre", "plugins", "dedrm.json")
    reference_json = os.path.join(fixed_dir, "dedrm  filled.json")
    
    # Create backup filename with timestamp in backups folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backups_dir = os.path.join(fixed_dir, "backups")
    os.makedirs(backups_dir, exist_ok=True)
    backup_json = os.path.join(backups_dir, f"dedrm_backup_{timestamp}.json")
    
    os.system('cls')  # Clear screen
    print_banner_and_version()
    print("==================================================")
    print("Phase 1: Key Extraction (Plugin-Compatible)")
    print("Phase 2: DeDRM Plugin Auto-Configuration")
    print("Phase 3: Calibre Auto-Import")
    print("Phase 4: Imported eBooks to EPUB Conversion")
    print("==================================================")
    print()

    try:
        # Cleanup any leftover temporary Kindle installations
        cleanup_temp_kindle()
        
        # Cleanup any leftover temp_extraction folder
        cleanup_temp_extraction()
        
        # === PRE-FLIGHT: CHECK FOR SAVED CONFIGURATION ===
        saved_config = load_config()
        
        if saved_config:
            # Check if configuration version matches current script version
            is_valid, config_version, current_version = check_config_version(saved_config)
            
            if not is_valid:
                # Version mismatch detected - force reconfiguration
                print_error("=" * 70)
                print_error("CONFIGURATION VERSION MISMATCH DETECTED!")
                print_error("=" * 70)
                print()
                print_warn(f"Saved Configuration Version: {config_version}")
                print_warn(f"Current Script Version:      {current_version}")
                print()
                print("The configuration format has changed and requires reconfiguration.")
                print("This ensures compatibility with new features and settings.")
                print()
                input("Press Enter to start the configuration wizard...")
                print()
                saved_config = configure_pre_flight_wizard(user_home)
            else:
                # Configuration exists and version matches - show options with timer
                action = prompt_config_action_with_timer(saved_config)
                
                if action == 'quit':
                    print_warn("Script cancelled by user")
                    return 0
                elif action == 'reconfigure':
                    print_step("Starting reconfiguration wizard...")
                    saved_config = configure_pre_flight_wizard(user_home)
                # else action == 'use', proceed with saved config
        else:
            # First run - show wizard
            print_step("First run detected - starting configuration wizard...")
            print()
            saved_config = configure_pre_flight_wizard(user_home)
        
        # Check if Calibre auto-import is enabled and ask to close Calibre NOW
        calibre_ready = False
        calibre_import_config = saved_config.get('calibre_import', {})
        if isinstance(calibre_import_config, dict) and calibre_import_config.get('enabled', False):
            print_step("Calibre Auto-Import is enabled")
            print("--------------------------------------------------")
            print()
            if not warn_close_calibre():
                print_warn("Calibre import will be skipped")
                calibre_ready = False
            else:
                calibre_ready = True
            print()
        
        # Use configured paths
        content_dir = saved_config.get('kindle_content_path')
        if not content_dir:
            # Fallback to interactive prompt if not in config
            default_content_dir = os.path.join(user_home, "Documents", "My Kindle Content")
            content_dir = get_kindle_content_path(default_content_dir)
        
        # === PHASE 1: KEY EXTRACTION ===
        # Clear screen if configured
        if saved_config.get('clear_screen_between_phases', True):
            os.system('cls')
        
        display_phase_banner(1, "Key Extraction")

        # Cleanup previous files
        for file_path in [output_key, output_k4i]:
            if os.path.exists(file_path):
                os.remove(file_path)
                print_ok(f"Previous {os.path.basename(file_path)} deleted.")
            else:
                print_warn(f"No existing {os.path.basename(file_path)} found.")

        print()
        
        # Extract keys using the extractor (since we need both txt and k4i files)
        print_step("Extracting Kindle keys...")
        print("--------------------------------------------------")
        print()
        
        success, dsn, tokens, extraction_stats = extract_keys_using_extractor(extractor, content_dir, output_key, output_k4i)
        
        print("--------------------------------------------------")
        print()
        
        # Check if extraction was successful
        if not success:
            if extraction_stats['total'] == 0:
                print_error("No books found in content directory!")
                return 1
            elif extraction_stats['success'] == 0:
                print_error("Key extraction failed! No keys were extracted from any books.")
                print_error(f"Failed: {extraction_stats['failed']} book(s)")
                if extraction_stats.get('failed_books'):
                    print()
                    print_warn("Failed books:")
                    for asin, title, error_msg in extraction_stats['failed_books'][:5]:
                        print(f"  - {asin}: {error_msg}")
                    if len(extraction_stats['failed_books']) > 5:
                        print(f"  ... and {len(extraction_stats['failed_books']) - 5} more")
                return 1
        
        # Display extraction results
        print_ok("Keys successfully extracted:")
        print(f"   - {output_key}")
        print(f"   - {output_k4i}")
        print()
        
        # Show extraction statistics
        if extraction_stats['total'] > 0:
            print_step("Extraction Statistics:")
            print(f"   Total books found: {extraction_stats['total']}")
            print(f"   Successfully extracted: {extraction_stats['success']}")
            if extraction_stats['failed'] > 0:
                print_warn(f"   Failed: {extraction_stats['failed']}")
        
        print()
        
        # Prevent Kindle auto-updates (if Kindle is installed)
        prevent_kindle_auto_update()
        
        # Display Phase 1 summary
        summary_points = [
            f"Processed {extraction_stats['total']} book(s) for key extraction",
            f"Successfully extracted keys from {extraction_stats['success']} book(s)",
            f"Generated kindlekey.txt at {output_key}",
            f"Generated kindlekey.k4i at {output_k4i}",
            "Kindle auto-update prevention configured"
        ]
        
        if extraction_stats['failed'] > 0:
            summary_points.append(f"Failed extractions: {extraction_stats['failed']} book(s) - see log for details")
        
        display_phase_summary(1, "Key Extraction", summary_points, pause_seconds=5)

        # === PHASE 2: DEDRM PLUGIN CONFIGURATION ===
        # Clear screen if configured
        if saved_config.get('clear_screen_between_phases', True):
            os.system('cls')
        
        display_phase_banner(2, "DeDRM Plugin Configuration")

        # Create backup if dedrm.json exists
        if os.path.exists(dedrm_json):
            print_step("Creating backup of existing dedrm.json...")
            shutil.copy2(dedrm_json, backup_json)
            print_ok(f"Backup created: {backup_json}")
        else:
            print_warn("No existing dedrm.json found - will create new one.")

        # Process the k4i file to create kindle key
        print_step("Processing kindlekey.k4i...")
        kindle_key = create_kindle_key_from_k4i(output_k4i, dsn, tokens)
        
        if not kindle_key:
            print_error("Failed to process k4i file!")
            return 1
            
        print_ok("Kindle key data processed successfully.")

        # Create the dedrm configuration
        print_step("Creating DeDRM configuration...")
        dedrm_config = create_dedrm_config(kindle_key, output_key, reference_json)

        # Write the JSON using the same method as the plugin: json.dump() with indent=2
        print_step("Writing dedrm.json with exact plugin formatting...")
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(dedrm_json), exist_ok=True)
        
        with open(dedrm_json, 'w') as f:
            json.dump(dedrm_config, f, indent=2)

        print_ok("DeDRM configuration updated successfully!")
        print_ok("Updated key: kindlekey")
        print_ok(f"Set extra key file: {output_key}")
        print()

        # Final verification
        print_step("Verifying configuration...")
        print()

        with open(dedrm_json, 'r') as f:
            dedrm_verify = json.load(f)
        
        # Count kindle keys
        key_count = len(dedrm_verify.get("kindlekeys", {}))
        
        # Get hide_sensitive flag
        hide_sensitive = saved_config.get('hide_sensitive_info', False)
        
        # Read voucher keys from kindlekey.txt
        voucher_keys = []
        if os.path.exists(output_key):
            try:
                with open(output_key, 'r') as f:
                    voucher_keys = [line.strip() for line in f if line.strip()]
            except Exception:
                pass
        
        # Table header (extra wide to fit 88-char base64 New Secret)
        print("┌─────────────────────────────┬────────────────────────────────────────────────────────────────────────────────────────────────┐")
        print("│ Configuration Item          │ Value                                                                                          │")
        print("├─────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────┤")
        
        # Total keys
        print(f"│ Total Kindle Keys           │ {str(key_count):<94} │")
        
        # Extra key file path
        extra_key_path = dedrm_verify.get('kindleextrakeyfile', 'Not set')
        if len(extra_key_path) > 94:
            extra_key_path = extra_key_path[:91] + "..."
        print(f"│ Extra Key File Path         │ {extra_key_path:<94} │")
        
        # Show key details with obfuscation if enabled
        if "kindlekeys" in dedrm_verify and "kindlekey" in dedrm_verify["kindlekeys"]:
            key_data = dedrm_verify["kindlekeys"]["kindlekey"]
            
            # DSN (full width, no truncation unless obfuscated)
            dsn_value = key_data.get('DSN', 'Not found')
            if hide_sensitive and dsn_value != 'Not found':
                dsn_value = obfuscate_sensitive(dsn_value)
            print(f"│ DSN                         │ {dsn_value:<94} │")
            
            # DSN_clear (if available)
            dsn_clear = key_data.get('DSN_clear', '')
            if dsn_clear:
                if hide_sensitive:
                    dsn_clear = obfuscate_sensitive(dsn_clear)
                print(f"│ DSN Clear                   │ {dsn_clear:<94} │")
            
            # Tokens (full width, no truncation unless obfuscated)
            tokens_value = key_data.get('kindle.account.tokens', '')
            if tokens_value:
                if hide_sensitive:
                    tokens_value = obfuscate_sensitive(tokens_value)
                print(f"│ Tokens                      │ {tokens_value:<94} │")
            
            # Show sample of secrets if available (obfuscated if needed)
            clear_old_secrets = key_data.get('kindle.account.clear_old_secrets', [])
            new_secrets = key_data.get('kindle.account.new_secrets', [])
            
            if clear_old_secrets:
                sample_clear_old = clear_old_secrets[0] if isinstance(clear_old_secrets, list) else str(clear_old_secrets)
                if hide_sensitive:
                    sample_clear_old = obfuscate_sensitive(sample_clear_old)
                print(f"│ Old Secret                  │ {sample_clear_old:<94} │")
            
            if new_secrets:
                sample_new_secret = new_secrets[0] if isinstance(new_secrets, list) else str(new_secrets)
                if hide_sensitive:
                    sample_new_secret = obfuscate_sensitive(sample_new_secret)
                print(f"│ New Secret                  │ {sample_new_secret:<94} │")
        
        # Voucher keys count at bottom
        print(f"│ Voucher Keys Count          │ {str(len(voucher_keys)):<94} │")
        
        # Table footer
        print("└─────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────┘")
        print()
        
        print_ok("Configuration verified successfully!")
        print()
        
        # Display Phase 2 summary
        summary_points = [
            "Processed kindlekey.k4i and created Kindle key data",
            "Updated DeDRM plugin configuration (dedrm.json)",
            f"Set extra key file path: {output_key}",
            "Added account keys to plugin database",
            f"Created configuration backup: {backup_json}",
            "Configuration verified successfully"
        ]
        
        display_phase_summary(2, "DeDRM Plugin Configuration", summary_points, pause_seconds=5)
        
        # === PHASE 3: CALIBRE AUTO-IMPORT ===
        imported_count = 0
        converted_count = 0
        import_results = None
        conversion_stats = None
        
        result = attempt_calibre_import(content_dir, script_dir, calibre_already_confirmed=calibre_ready, extraction_stats=extraction_stats)
        
        # Handle result - could be 0 (skipped), or tuple (imported_count, book_ids, config, results)
        if result == 0:
            imported_count = 0
        elif isinstance(result, tuple):
            if len(result) == 4:
                # New format with results dict
                imported_count, book_ids, config, import_results = result
            else:
                # Old format without results dict (backward compatibility)
                imported_count, book_ids, config = result
                import_results = None
            
            # === PHASE 4: KFX TO EPUB CONVERSION ===
            if config.get('convert_to_epub', False) and book_ids:
                conversion_stats = process_book_conversions(config['library_path'], book_ids, config)
                converted_count = conversion_stats['merged']
        else:
            imported_count = result if result is not None else 0
        
        # Clear screen only if configured to do so
        if saved_config.get('clear_screen_between_phases', True):
            os.system('cls')
        
        print("==================================================")
        print_done("SUCCESS! Complete automation finished!")
        print("==================================================")
        print()
        print_ok("What was accomplished:")
        print("  + Extracted Kindle keys using plugin-compatible method")
        print("  + Generated kindlekey.txt (voucher keys)")
        print("  + Generated kindlekey.k4i (account data)")
        print("  + Updated DeDRM plugin configuration automatically")
        print("  + Used exact same JSON generation as the plugin")
        print("  + Set extra key file path in plugin")
        print("  + Added account keys to plugin database")
        print("  + Created configuration backup for safety")
        if imported_count > 0:
            print(f"  + Imported {imported_count} ebook(s) to Calibre")
        if converted_count > 0:
            print(f"  + Converted and merged {converted_count} ebook(s) to EPUB format")
        
        # Show extraction issues if any
        if extraction_stats and extraction_stats.get('failed', 0) > 0:
            print()
            print_warn(f"Extraction Issues: {extraction_stats['failed']} book(s) failed key extraction")
            if extraction_stats.get('failed_books'):
                print("      Failed books:")
                for asin, title, error_msg in extraction_stats['failed_books']:
                    print(f"        - {asin} - {title}")
        
        # Show import/conversion issues if any
        if import_results and isinstance(import_results, dict):
            # Show skipped books (duplicates) with book titles
            if import_results.get('skipped', 0) > 0:
                print()
                # Print header in RED and BOLD
                print(f"\033[1m\033[91m[!] Import Issues: {import_results['skipped']} book(s) already exist in database\033[0m")
                if import_results.get('skipped_books'):
                    print("      Skipped books:")
                    for asin, title in import_results['skipped_books']:
                        print(f"        - {asin} - {title}")
            
            if import_results.get('failed', 0) > 0:
                print()
                print_warn(f"Import Issues: {import_results['failed']} book(s) failed to import")
                if import_results.get('failed_books'):
                    print("      Failed books:")
                    for book_name, _ in import_results['failed_books'][:5]:
                        print(f"        - {book_name}")
                    if len(import_results['failed_books']) > 5:
                        print(f"        ... and {len(import_results['failed_books']) - 5} more")
            
            if import_results.get('timed_out', 0) > 0:
                print()
                print_warn(f"Import Timeouts: {import_results['timed_out']} book(s) timed out")
                if import_results.get('timed_out_books'):
                    print("      Timed out books:")
                    for book_name in import_results['timed_out_books'][:5]:
                        print(f"        - {book_name}")
                    if len(import_results['timed_out_books']) > 5:
                        print(f"        ... and {len(import_results['timed_out_books']) - 5} more")
        
        if conversion_stats and isinstance(conversion_stats, dict):
            if conversion_stats.get('failed', 0) > 0:
                print()
                print_warn(f"Conversion Issues: {conversion_stats['failed']} book(s) failed to convert")
                if conversion_stats.get('failed_conversions'):
                    print("      Failed conversions:")
                    for book_id, title, author, _ in conversion_stats['failed_conversions'][:5]:
                        print(f"        - {title} by {author}")
                    if len(conversion_stats['failed_conversions']) > 5:
                        print(f"        ... and {len(conversion_stats['failed_conversions']) - 5} more")
            
            if conversion_stats.get('skipped_kfx_zip', 0) > 0:
                print()
                print_warn(f"Conversion Skipped: {conversion_stats['skipped_kfx_zip']} .kfx-zip file(s) skipped")
        
        # Determine if we should pause based on errors and skip_phase_pauses setting
        has_errors = False
        if extraction_stats and extraction_stats.get('failed', 0) > 0:
            has_errors = True
        if import_results and isinstance(import_results, dict):
            if import_results.get('skipped', 0) > 0 or import_results.get('failed', 0) > 0 or import_results.get('timed_out', 0) > 0:
                has_errors = True
        if conversion_stats and isinstance(conversion_stats, dict):
            if conversion_stats.get('failed', 0) > 0 or conversion_stats.get('skipped_kfx_zip', 0) > 0:
                has_errors = True
        
        # Always pause if there are errors, otherwise respect skip_phase_pauses setting
        skip_pauses = saved_config.get('skip_phase_pauses', False) if saved_config else False
        should_pause = has_errors or not skip_pauses
        
        if should_pause:
            print()
            print("Press Any key to continue...")
            msvcrt.getch()
        
        os.system('cls')
        print()
        print_banner_and_version()
        print("For the latest version of this script and updates, visit:")
        print_colored("https://techy-notes.com/blog/dedrm-v10-0-14-tutorial", 'cyan')
        print()
        print("Watch the video tutorial on YouTube:")
        print_colored("https://www.youtube.com/watch?v=pkii6EQEeGs", 'cyan')
        print()
        print_warn("Please subscribe to the YouTube channel!")
        print("Your support and appreciation is greatly valued.")
        print()
        print("If you'd like to show extra support this Script, consider buying me a Beer!:")
        print_colored("https://buymeacoffee.com/jadehawk", 'cyan')
        print()
        print("--------------------------------------------------")
        print_step("CREDITS")
        print("--------------------------------------------------")
        print()
        print("This script is powered by KFXKeyExtractor28.exe")
        print("Created/Modded by: Satsuoni")
        print()
        print("KFXKeyExtractor is the CORE tool that makes this automation possible.")
        print("It extracts Kindle DRM keys from your Kindle for PC installation,")
        print("enabling the DeDRM process for your purchased ebooks.")
        print()
        print("Visit Satsuoni's GitHub profile:")
        print_colored("https://github.com/Satsuoni", 'cyan')
        print()
        print("For the DeDRM tools repository:")
        print_colored("https://github.com/Satsuoni/DeDRM_tools", 'cyan')
        print()
        print("Thank you, Satsuoni, for creating and maintaining this essential tool!")

    except Exception as e:
        print_error(f"Script failed: {str(e)}")
        import traceback
        print_error(f"Traceback: {traceback.format_exc()}")
        
        # Restore backup if it exists
        if os.path.exists(backup_json) and os.path.exists(dedrm_json):
            print_warn("Restoring backup...")
            shutil.copy2(backup_json, dedrm_json)
            print_ok("Backup restored.")
        
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
