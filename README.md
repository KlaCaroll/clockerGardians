# ‶츏 Clocker

A lightweight, autonomous, and privacy-focused menu bar time tracker designed natively for macOS.

Clocker runs discreetly in the macOS menu bar, logging only active work time. It automatically pauses tracking whenever your Mac goes to sleep, locks the screen, or turns off the display, and resumes seamlessly upon wake or unlock.

---

## ✨ Features

- Wero-Friction Passive Tracking: Automatically detects lock, sleep, and display sleep events via macOS AppKit and Foundation notification centers.
- Native Menu Bar Interface: Built directly on Cocoa's NSStatusBar for immediate, crystal-clear text display (➱️ 00h 00m) without dock clutter or background window artifacts.
- Dedicated Isolated Storage: Organizes weekly structured text reports cleanly inside a dedicated Clocker_Reports subfolder.
- Custom Location Picker: Change the reports directory on the fly via standard macOS directory chooser dialogs.
- On-Demand Sync: Instantly flush and persist the running session to disk using the Save / Sync Now menu item (or Cmd + S).n- Autonomous & Standalone: Distributed as a redistributable, self-contained .dmg installer requiring no terminal setup or Python installation.

---

## 🚀 Installation & Usage

### Option A: Standalone macOS Application (.dmg)

No terminal or technical expertise is required:
1. Download Clocker-macOS.dmg from the Releases section of this repository.
2. Double-click the downloaded .dmg file to mount it.
3. Drag and drop the Clocker icon into the Applications folder shortcut.
4. Launch Clocker from your Applications folder or Spotlight (Cmd + Space).

> **Important Note on macOS First Launch (Gatekeeper):**  
> Because Clocker is an unsigned open-source application, macOS may verify its source on first launch.  
> To open it: **Right-click (or Control-click)** Clocker.app in /Applications, select Open, and click Open in the confirmation dialog. (Or go to System Settings > Privacy & Security and click Open Anyway). This step is only required on the very first start.

---

### Option B: Run from Source (Developers)

Prerequisites: macOS 11+, Python 3.10+

1. Clone the repository:
   git clone https://github.com/klacaroll/clockerGardians.git
   cd clockerGardians

2. Create and activate a virtual environment:
   python3 -m venv .venv
   source .venv/bin/activate

3. Install required native dependencies:
   pip install --upgrade pip
   pip install pyobjc-framework-Cocoa pyobjc-framework-Quartz

4. Run the application:
   python clock_app.py

---

## 🧭 Menu Controls

Clicking the clock icon in your menu bar displays:

- Today: XXh XXm
  Shows cumulative active work duration tracked for the current day.

- This week: XXh XXm
  Shows cumulative active work duration tracked for the current calendar week.

- Save / Sync Now [Cmd + S]
  Immediately writes ongoing session time to the weekly report file.

- Open Reports Folder
  Opens the dedicated Clocker_Reports directory in Finder.

- Change Reports Location...
  Opens a native panel to choose a new destination folder.

- Quit Clocker [Cmd + Q]
  Stops time tracking, finalizes the session, and exits cleanly.

---

## 🤩 Packaging (.dmg)

To build the standalone application bundle and disk image locally:

1. Ensure create-dmg is installed:
   brew install create-dmg

2. Run the packagging script:
   ./build_dmg.sh

The resulting distribution file will be available under:  
dist/dmg/Clocker-macOS.dmg

---

## 📂 Storage & Configuration

- Configuration File: ~Local/Application Support/Clocker/config.json
- Reports Directory: <Selected_Folder>/Clocker_Reports/ (defaults to ~/Documents/Clocker_Reports/)
- File Format: Weekly plain text reports named rapport_temps_semaine_<WEEK>_<YEAR>.txt

---

## 🗺 Roadmap & Future Storage

Clocker currently favors zero-dependency, human-readable plain text reports that require no external database viewer. An internal SQLite storage backend will likely be integrated in future releases based on community demand to enable granular analytics and complex querying while preserving plain text exports.

---

## 📦 License

This project is open-source and available under the MIT License.
