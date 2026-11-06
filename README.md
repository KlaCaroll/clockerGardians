================================================================================
                                ⏱️  CLOCKER
================================================================================

A lightweight, autonomous, and privacy-focused menu bar time tracker designed
natively for macOS.

Clocker runs discreetly in the macOS menu bar, logging only active work time.
It automatically pauses tracking whenever your Mac goes to sleep, locks the
screen, or turns off the display, and resumes seamlessly upon wake or unlock.


--------------------------------------------------------------------------------
1. KEY FEATURES
--------------------------------------------------------------------------------

- Zero-Friction Passive Tracking:
  Automatically detects lock, sleep, and display sleep events using macOS
  AppKit and Foundation notification centers.

- Native Menu Bar Interface:
  Built directly on Cocoa's NSStatusBar for clean text rendering (e.g. ⏱️ 00h 00m)
  without dock clutter or background window artifacts.

- Dedicated Isolated Storage:
  Organizes weekly plain text reports cleanly inside a dedicated Clocker_Reports
  subfolder.

- Custom Directory Picker:
  Change reports storage location at any time via a native macOS folder chooser.

- On-Demand Sync:
  Immediately persist the running session to disk using "Save / Sync Now"
  or the Cmd + S keyboard shortcut.

- Autonomous & Portable:
  Distributed as a standalone .dmg package requiring no Python setup or
  terminal knowledge for end users.


--------------------------------------------------------------------------------
2. INSTALLATION GUIDE (FOR ALL USERS)
--------------------------------------------------------------------------------

No terminal or technical expertise is required:

Step 1: Download
  Get the latest Clocker-macOS.dmg installer package.

Step 2: Install
  Double-click the .dmg file to open it. Drag the "Clocker" application icon
  and drop it directly into the "Applications" shortcut folder.

Step 3: Launch
  Open your Applications folder (or press Cmd + Space for Spotlight) and launch
  Clocker.

FIRST-TIME macOS SECURITY NOTE (Gatekeeper):
  Because Clocker is distributed directly as open-source software, macOS will
  verify its source on first launch.
  If an alert appears:
  - Right-click (or Control-click) on Clocker in your Applications folder.
  - Select "Open" from the context menu.
  - Confirm by clicking "Open" in the prompt dialog.
  (Alternatively: go to System Settings > Privacy & Security, scroll down and
  click "Open Anyway").
  This step is only required on the very first start.


--------------------------------------------------------------------------------
3. RUNNING FROM SOURCE (FOR DEVELOPERS)
--------------------------------------------------------------------------------

Prerequisites: macOS 11+, Python 3.10+

1. Clone repository:
   git clone https://github.com/klacaroll/clockerGardians.git
   cd clockerGardians

2. Create virtual environment:
   python3 -m venv .venv
   source .venv/bin/activate

3. Install required native dependencies:
   pip install --upgrade pip
   pip install pyobjc-framework-Cocoa pyobjc-framework-Quartz

4. Run application:
   python clock_app.py


--------------------------------------------------------------------------------
4. MENU BAR CONTROLS
--------------------------------------------------------------------------------

Clicking the clock icon in your status bar provides the following menu:

- Today: XXh XXm
  Shows cumulative active work duration tracked for the current day.

- This week: XXh XXm
  Shows cumulative active work duration tracked for the current calendar week.

- Save / Sync Now  [Cmd + S]
  Immediately writes ongoing session time to the weekly report file.

- Open Reports Folder
  Opens the Clocker_Reports directory directly in Finder.

- Change Reports Location...
  Opens a native macOS folder selector to relocate future and active logs.

- Quit Clocker  [Cmd + Q]
  Stops time tracking, finalizes the session, and exits cleanly.


--------------------------------------------------------------------------------
5. PACKAGING THE STANDALONE DMG
--------------------------------------------------------------------------------

To produce the redistributable installer locally:

1. Ensure create-dmg is installed:
   brew install create-dmg

2. Run the packaging script:
   ./build_dmg.sh

The compiled and signed disk image will be placed in:
dist/dmg/Clocker-macOS.dmg


--------------------------------------------------------------------------------
6. STORAGE & FILE STRUCTURE
--------------------------------------------------------------------------------

- Configuration File:
  ~/Library/Application Support/Clocker/config.json

- Reports Directory:
  <Selected_Folder>/Clocker_Reports/
  (Defaults to ~/Documents/Clocker_Reports/)

- Report File Naming:
  rapport_temps_semaine_<WEEK_NUMBER>_<YEAR>.txt


--------------------------------------------------------------------------------
7. LICENSE
--------------------------------------------------------------------------------

This project is licensed under the MIT License.