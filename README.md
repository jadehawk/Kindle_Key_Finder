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

**Version 2025.11.07.JH**

- Initial public release
- Four-phase automation workflow
- Comprehensive configuration wizard
- Advanced logging system
- Calibre auto-import and EPUB conversion

---

**Note**: This is an automation wrapper around KFXKeyExtractor28.exe. All credit for the core key extraction functionality goes to Satsuoni.
