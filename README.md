# Kindle Key Finder - Python Edition

[![Windows](https://img.shields.io/badge/platform-Windows%2011-blue.svg)](https://www.microsoft.com/windows)
[![Python](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A comprehensive automation tool for extracting Kindle DRM keys and automatically configuring the Calibre DeDRM plugin. This script streamlines the entire DeDRM workflow from key extraction to EPUB conversion.

## Features

### Core Functionality

- **Automated Key Extraction** - Extracts DRM keys from your Kindle for PC installation
- **DeDRM Plugin Integration** - Automatically configures Calibre's DeDRM plugin
- **Calibre Auto-Import** - Imports and processes all your Kindle books
- **KFX to EPUB Conversion** - Converts imported books to EPUB format
- **Per-Book Processing** - Processes each book individually with timeout protection

### Smart Automation

- **One-Click Operation** - Complete automation from start to finish
- **Configuration Wizard** - Interactive setup for first-run configuration
- **Saved Preferences** - Remembers settings for future runs
- **Auto-Update Prevention** - Configures Kindle to prevent automatic updates
- **Backup System** - Creates timestamped backups before making changes

### Advanced Features

- **Privacy Protection** - Optional obfuscation of sensitive data in console output
- **Detailed Logging** - Comprehensive logs for troubleshooting
- **Duplicate Detection** - Handles books already in your Calibre library
- **Smart Cleanup** - Manages KFX-ZIP files and source file cleanup
- **Failed Book Exclusion** - Skips books that failed key extraction
- **Book Title Fetching** - Optional Amazon metadata lookup for better identification
- **Multi-Phase Operation** - Organized workflow with clear phase banners and summaries

## Requirements

### System Requirements

- **Operating System**: Windows 11 (Windows-specific paths and tools)
- **Python**: 3.6 or higher
- **Kindle for PC**: Installed and signed in to your Amazon account

### Required Software

- [Calibre](https://calibre-ebook.com/) - E-book management software
- [DeDRM Plugin](https://github.com/Satsuoni/DeDRM_tools) - DeDRM tools for Calibre
- [KFXKeyExtractor28.exe](https://github.com/Satsuoni/DeDRM_tools) - Key extraction tool by Satsuoni

### Python Dependencies

No external Python packages required - uses only standard library modules:

- `os`, `sys`, `json`, `subprocess`, `shutil`, `time`, `threading`, `msvcrt`, `platform`, `datetime`

## Installation

1. **Clone or Download** this repository:

   ```bash
   git clone https://github.com/yourusername/Kindle_Key_Finder.git
   cd Kindle_Key_Finder
   ```

2. **Place KFXKeyExtractor28.exe** in the same directory as `key_finder.py`

3. **Install Calibre** and the **DeDRM plugin** if not already installed

4. **Sign in to Kindle for PC** with your Amazon account

## Usage

### First Run

Simply run the script:

```bash
python key_finder.py
```

Or use the provided batch file:

```bash
Run Key_finder.bat
```

The script will guide you through:

1. **Configuration Wizard** - Set up your preferences
2. **Kindle Content Path** - Specify your Kindle library location
3. **Privacy Settings** - Choose whether to hide sensitive data
4. **Display Options** - Configure visual preferences
5. **Calibre Integration** - Set up automatic import

### Subsequent Runs

The script will:

- Load your saved configuration
- Auto-proceed after 10 seconds (or press any key for options)
- Allow reconfiguration or deletion of saved settings

## Directory Structure

```
Kindle_Key_Finder/
├── key_finder.py              # Main script
├── key_finder_config.json     # Saved configuration
├── KFXKeyExtractor28.exe      # Key extraction tool
├── Run Key_finder.bat         # Batch launcher
├── Keys/
│   ├── kindlekey.txt          # Extracted voucher keys
│   └── kindlekey.k4i          # Account data
├── backups/
│   └── dedrm_backup_*.json    # DeDRM config backups
└── Logs/
    ├── extraction_logs/       # Key extraction logs
    ├── import_logs/           # Calibre import logs
    └── conversion_logs/       # EPUB conversion logs
```

## Configuration Options

### Kindle Content Path

- Default: `%USERPROFILE%\Documents\My Kindle Content`
- Customizable during setup

### Privacy Settings

- Hide sensitive information (DSN, tokens, keys) in console output
- Obfuscates data while maintaining visibility

### Calibre Integration

- **Library Path**: Your Calibre library location
- **Convert to EPUB**: Automatically convert KFX books
- **KFX-ZIP Handling**: Skip or convert DRM-protected files
- **Source Management**: Keep, delete, or smart cleanup after conversion

### Display Options

- **Fetch Book Titles**: Query Amazon for book metadata (slower)
- **Clear Screen**: Clean output between phases

## Workflow Phases

### Phase 1: Key Extraction

- Scans Kindle Content directory
- Extracts keys from each book
- Generates `kindlekey.txt` and `kindlekey.k4i`
- Creates detailed extraction logs

### Phase 2: DeDRM Plugin Configuration

- Backs up existing DeDRM configuration
- Updates plugin with extracted keys
- Sets extra key file path
- Verifies configuration

### Phase 3: Calibre Auto-Import

- Detects and handles duplicate books
- Imports all DeDRM'd ebooks
- Processes with 60-second timeout per book
- Excludes books that failed extraction

### Phase 4: KFX to EPUB Conversion

- Converts imported KFX books to EPUB
- Merges EPUB format into existing records
- Handles source file management
- Creates conversion logs

## Logging

The script creates detailed logs in the `Logs/` directory:

- **Extraction Logs**: Failed book extractions with error details
- **Import Logs**: Failed imports, timeouts, and errors
- **Conversion Logs**: Failed conversions and skipped books

All logs are timestamped for easy tracking.

## Important Notes

### Calibre Must Be Closed

The script requires Calibre to be closed during:

- Configuration file access
- Database operations
- Book imports

The script will verify Calibre is closed before proceeding.

### Windows-Only

This script is designed specifically for Windows due to:

- Windows-specific file paths
- Kindle for PC installation locations
- Calibre configuration file locations

For other operating systems, see manual extraction instructions in the script output.

### DRM-Protected Files

- Books with `.kfx-zip` extension may indicate DRM protection failure
- Configure handling in Calibre settings (skip or attempt conversion)

## Troubleshooting

### Key Extraction Fails

- Ensure Kindle for PC is installed and signed in
- Check that books are downloaded in Kindle for PC
- Review extraction logs in `Logs/extraction_logs/`

### Import Timeouts

- Default timeout is 60 seconds per book
- Large books may need more time
- Check import logs in `Logs/import_logs/`

### Conversion Failures

- Verify DeDRM plugin is properly installed
- Check conversion logs in `Logs/conversion_logs/`
- Some DRM-protected files cannot be converted

## Credits

This script is powered by **KFXKeyExtractor28.exe**

**Created / Modded by**: [Satsuoni](https://github.com/Satsuoni)

KFXKeyExtractor is the core tool that makes this automation possible. It extracts Kindle DRM keys from your Kindle for PC installation, enabling the DeDRM process for your purchased ebooks.

### Resources

- [Satsuoni's GitHub](https://github.com/Satsuoni)
- [DeDRM Tools Repository](https://github.com/Satsuoni/DeDRM_tools)

Thank you, Satsuoni, for creating and maintaining this essential tool!

## Additional Resources

- [Tutorial Blog Post](https://techy-notes.com/blog/dedrm-v10-0-14-tutorial)
- [Video Tutorial on YouTube](https://www.youtube.com/watch?v=pkii6EQEeGs)

## Support

If you find this script helpful, consider:

- Subscribing to the [YouTube channel](https://www.youtube.com/watch?v=pkii6EQEeGs)
- [Buying me a coffee](https://buymeacoffee.com/jadehawk)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Legal Disclaimer

This tool is intended for use with ebooks you have legally purchased. Users are responsible for complying with copyright laws and terms of service agreements. The authors of this script do not condone piracy or copyright infringement.

## Version History

**Version 2025.11.21.JH**

Cloud Folder Detection & Write Permission Enhancement:

- **Proactive Cloud Folder Detection**: Script now detects and avoids cloud-synced locations before attempting write operations
  - Added `is_cloud_synced_location()` helper function to identify cloud sync folders
  - Detects OneDrive, Google Drive, Dropbox, iCloud, Box, and Sync.com folders
  - Prevents intermittent "Access Denied" errors during temp directory creation
  - Cloud folders can cause sync conflicts during extraction operations
- **Enhanced Write Permission Checks**: Improved `check_write_permissions()` with two-tier validation
  - First check: Detects if directory is in a cloud-synced location
  - Second check: Tests actual directory creation capability (not just file writes)
  - Provides clear error messages explaining why fallback location is being used
  - Returns both status and detailed error message for better user feedback
- **Improved Validation Messaging**: Updated Pre-Flight validation display
  - Shows specific cloud service name when detected (e.g., "OneDrive", "Google Drive")
  - Explains potential issues with cloud folders (sync conflicts, access errors)
  - Displays fallback path location for user awareness
  - Added visual warning when cloud folder is detected
- **Reliability Improvements**: Prevents class of errors caused by cloud sync interference
  - Eliminates timing-dependent access issues during temp folder operations
  - Ensures consistent behavior regardless of sync state
  - Provides deterministic fallback path selection

Updated Functions:

- `is_cloud_synced_location()` - New helper to detect cloud sync folders
- `check_write_permissions()` - Enhanced with cloud detection + directory creation test
- `validate_all_requirements()` - Updated to handle cloud folder detection results
- `display_validation_results()` - Shows detailed cloud folder warnings when detected

**Version 2025.11.15.JH**

Calibre Auto-Continue & Failsafe Key Cleanup:

- **Calibre Auto-Continue**: Script now automatically continues once Calibre is detected as closed
  - Removed manual "Press Enter to continue" prompts after closing Calibre
  - Added real-time process detection loop that monitors for Calibre closure
  - Applies to both pre-flight configuration and Phase 3 import preparation
  - Provides clear status messages: "Waiting for Calibre to close..." → "Calibre has closed - continuing with script..."
  - Improves user experience by eliminating unnecessary manual confirmations
- **Failsafe Key Cleanup**: Enhanced Phase 1 key cleanup to check both possible storage locations
  - Cleans up keys from BOTH script directory and AppData fallback location
  - Prevents confusing "No existing kindlekey.txt found" warnings
  - Ensures clean slate regardless of which location was used in previous run
  - Silent operation when no keys exist (first run scenario)
  - Shows confirmation only when files are actually deleted
  - Handles edge case where validation determines different working directory between runs

Updated Functions:

- `warn_close_calibre()` - Now auto-continues when Calibre closes (no manual prompt)
- `verify_calibre_closed_with_loop()` - Simplified to pure auto-detection (removed manual option)
- `prompt_calibre_import_settings()` - Auto-continues after Calibre closes during configuration
- Phase 1 cleanup logic - Checks both script_dir/Keys and AppData/Keys locations

**Version 2025.11.13.JH**

Fallback Path System & Write-Protected Directory Support:

- Implemented comprehensive fallback path system for write-protected directories
- Added automatic detection and handling of read-only script locations (network drives, restricted folders)
- Created `%LOCALAPPDATA%\Kindle_Key_Finder` fallback location for all operations
- Updated all file operations to respect fallback paths:
  - Configuration files (key_finder_config.json)
  - Extracted keys (Keys/kindlekey.txt, Keys/kindlekey.k4i)
  - Processing logs (Logs/extraction_logs/, import_logs/, conversion_logs/)
  - Book history tracking (history.txt)
  - Temporary extraction folders (temp_extraction/)
  - Configuration backups (backups/dedrm*backup*\*.json)
- Added `_LOCATION_INFO.txt` marker file to help users locate their files
- Implemented smart config migration between script directory and AppData
- Fixed `discover_config_location()` to prioritize writable script directory
- Prevents config duplication when moving between protected/unprotected folders
- All log writing functions now use validated working directory
- Book history tracking properly uses fallback paths
- Temporary file operations respect fallback location

New Functions Added:

- `check_write_permissions()` - Tests directory writeability
- `get_disk_space()` - Retrieves disk space information
- `get_fallback_paths()` - Generates fallback directory structure
- `discover_config_location()` - Smart config path discovery with migration logic
- `create_location_marker()` - Creates helper file for users to locate their data
- `migrate_config_to_fallback()` - Handles config migration between locations

**Version 2025.11.09.JH**

Auto-Launch Kindle & Book History Tracking:

- Added Auto-Launch Kindle feature with configuration option
- Script can now automatically launch Kindle.exe and wait for it to close
- Validates books are present before proceeding with extraction
- Implemented book processing history tracking system (history.txt)
- Tracks ASINs of successfully processed books
- Prompts user to skip previously processed books or re-process all
- History tracking integrated across all phases (extraction, import, final summary)
- Skipped books are excluded from Calibre import to prevent duplicates
- Added detailed display of skipped books in final summary with ASINs and titles
- Fixed display_config_summary to show Auto-Launch Kindle setting

**Version 2025.11.08.JH**

Configuration Management & Version Tracking:

- Added SCRIPT_VERSION constant for tracking script versions
- Implemented configuration version validation system
- Auto-detects version mismatches and forces reconfiguration when needed
- Saves script version to config file on every save operation
- Prevents issues when new configuration flags are added in updates

Smart Pause & Error Handling:

- Added intelligent pause detection at final summary screen
- Always pauses when ANY errors are detected (extraction, import, conversion)
- Respects skip_phase_pauses setting only when execution is error-free
- Ensures users never miss critical error information

AZW3 Support & Format Flexibility:

- Implemented two-step AZW3→MOBI→EPUB conversion for better quality
- Added smart format detection to route AZW3 vs other formats appropriately
- Replaced hardcoded 'KFX' deletion with dynamic source format detection
- Updated terminology from 'KFX' to generic 'source format' throughout
- Changed config value from `delete_kfx` to `delete_source`
- Added temp_extraction folder cleanup after Phase 4 completion
- Removed legacy config support (version checking handles upgrades)
- Fixed conversion issues with AZW3 files
- Enabled proper source file management for all Kindle formats (KFX, AZW, AZW3, KFX-ZIP)

**Version 2025.11.07.JH**

- Initial public release
- Four-phase automation workflow
- Comprehensive configuration wizard
- Advanced logging system
- Calibre auto-import and EPUB conversion

---

**Note**: This is an automation wrapper around KFXKeyExtractor28.exe. All credit for the core key extraction functionality goes to Satsuoni.
