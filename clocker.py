import os
import json
import subprocess
from datetime import datetime
import objc

from Foundation import (
    NSObject,
    NSDistributedNotificationCenter,
    NSWorkspace
)
from AppKit import (
    NSApplication,
    NSOpenPanel,
    NSModalResponseOK
)
import Quartz


# Global tracking state
active_session_start = None
active_lock_start = None


def log_debug(message):
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"[{current_time}] 🔍 {message}")


def get_config_directory():
    app_support = os.path.expanduser("~/Library/Application Support/Clocker")
    os.makedirs(app_support, exist_ok=True)
    return app_support


def get_config_filepath():
    return os.path.join(get_config_directory(), "config.json")


def save_custom_report_directory(chosen_path):
    config_file = get_config_filepath()
    try:
        clean_path = str(chosen_path).strip()
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({"report_directory": clean_path}, f, indent=2)
        log_debug(f"Report directory updated to: {clean_path}")
    except Exception as e:
        log_debug(f"Configuration save error: {e}")


def choose_report_directory_dialog():
    app = NSApplication.sharedApplication()
    app.activateIgnoringOtherApps_(True)
    panel = NSOpenPanel.openPanel()
    panel.setTitle_("Choose Reports Folder")
    panel.setMessage_("Select the destination folder for Clocker reports:")
    panel.setCanChooseFiles_(False)
    panel.setCanChooseDirectories_(True)
    panel.setAllowsMultipleSelection_(False)
    panel.setCanCreateDirectories_(True)
    panel.setPrompt_("Select")

    if panel.runModal() == NSModalResponseOK:
        urls = panel.URLs()
        if urls and len(urls) > 0:
            selected_path = str(urls[0].path())
            save_custom_report_directory(selected_path)
            return selected_path
    return None


def get_report_directory():
    config_file = get_config_filepath()
    target_dir = None

    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                target_dir = data.get("report_directory")
        except Exception as e:
            log_debug(f"Error reading configuration: {e}")

    if not target_dir or not os.path.exists(target_dir):
        target_dir = os.path.expanduser("~/Documents")

    reports_folder = os.path.join(target_dir, "Clocker_Reports")
    os.makedirs(reports_folder, exist_ok=True)
    return reports_folder


def get_log_filepath(date_obj):
    reports_dir = get_report_directory()
    cal = date_obj.isocalendar()
    filename = f"rapport_temps_semaine_{cal[1]}_{cal[0]}.txt"
    return os.path.join(reports_dir, filename)


def format_duration(seconds):
    total_seconds = max(0, int(seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}h {minutes:02d}m {secs:02d}s"


def read_history(filepath):
    sessions = []
    if not os.path.exists(filepath):
        return sessions

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("[") or " -> " not in line:
                continue

            try:
                parts = line.split(" -> ")
                start_part = parts[0].strip("[ ]")
                end_part = parts[1].split(" | ")[0].strip()

                start_dt = datetime.strptime(start_part, "%Y-%m-%d %H:%M:%S")
                end_dt = datetime.strptime(end_part, "%Y-%m-%d %H:%M:%S")
                duration_minutes = (end_dt - start_dt).total_seconds() / 60.0

                sessions.append({
                    "start": start_dt,
                    "end": end_dt,
                    "duration": duration_minutes
                })
            except Exception:
                continue

    return sessions


def calculate_totals(sessions, now):
    day_total = 0.0
    week_total = 0.0
    current_cal = now.isocalendar()

    for s in sessions:
        s_start = s["start"]
        s_cal = s_start.isocalendar()

        if s_cal[0] == current_cal[0] and s_cal[1] == current_cal[1]:
            week_total += s["duration"]
            if s_start.date() == now.date():
                day_total += s["duration"]

    global active_session_start
    if active_session_start is not None:
        elapsed = (now - active_session_start).total_seconds() / 60.0
        day_total += elapsed
        week_total += elapsed

    return day_total, week_total


def rewrite_report_file(filepath, sessions, now):
    header = (
        "================================================================================\n"
        "                                CLOCKER REPORT                                 \n"
        "================================================================================\n\n"
    )

    day_total, week_total = calculate_totals(sessions, now)

    summary = (
        f"Generated at: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Today's Total:     {format_duration(day_total * 60)}\n"
        f"This Week's Total: {format_duration(week_total * 60)}\n\n"
        "--------------------------------------------------------------------------------\n"
        "SESSION DETAILS\n"
        "--------------------------------------------------------------------------------\n"
    )

    note = (
        "NOTE:\n"
        "Because the tracker relies on screen unlock status, short breaks away from the desk\n"
        "(such as grabbing water, using the restroom, or walking across the office) are not deducted\n"
        "unless the screen is locked.\n"
        "Similarly, standard statutory breaks (e.g., 15-minute breaks) are not automatically factored in.\n"
        "As a result, this total may slightly underestimate or differ from your actual billable work hours.\n"
    )

    nb = (
        "N.B. (Nota Bene):\n"
        "For the most accurate records, remember to lock your screen (Cmd + Ctrl + Q) whenever you step away.\n"
    )

    disclaimer = f"\n--------------------------------------------------------------------------------\n{note}\n{nb}"

    body_lines = []
    for s in sessions:
        dur_str = format_duration(s["duration"] * 60)
        start_str = s["start"].strftime("%Y-%m-%d %H:%M:%S")
        end_str = s["end"].strftime("%Y-%m-%d %H:%M:%S")
        body_lines.append(f"[{start_str}] -> [{end_str}] | Active: {dur_str}")

    content = header + summary + "\n".join(body_lines) + "\n" + disclaimer + "\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def start_session():
    global active_session_start, active_lock_start
    if active_session_start is None:
        active_session_start = datetime.now()
        active_lock_start = None
        log_debug(f"SESSION STARTED: {active_session_start.strftime('%Y-%m-%d %H:%M:%S')}")


def stop_session(reason=""):
    global active_session_start
    if active_session_start is None:
        return

    now = datetime.now()
    filepath = get_log_filepath(now)
    duration_min = (now - active_session_start).total_seconds() / 60.0

    sessions = read_history(filepath)
    sessions.append({
        "start": active_session_start,
        "end": now,
        "duration": duration_min
    })

    rewrite_report_file(filepath, sessions, now)
    log_debug(f"SESSION STOPPED: {reason} ({format_duration(duration_min * 60)})")
    active_session_start = None


def save_current_state():
    now = datetime.now()
    filepath = get_log_filepath(now)
    stop_session("Manual sync requested")
    start_session()
    log_debug(f"Manual sync completed to: {filepath}")
    return filepath


class SystemEventsObserver(NSObject):
    def screenLocked_(self, notification):
        global active_lock_start
        active_lock_start = datetime.now()
        stop_session("Screen locked")

    def screenUnlocked_(self, notification):
        global active_lock_start
        start_session()
        active_lock_start = None

    def sleepNotification_(self, notification):
        stop_session("System sleep")

    def wakeNotification_(self, notification):
        start_session()


def setup_observers():
    observer = SystemEventsObserver.alloc().init()
    dist_center = NSDistributedNotificationCenter.defaultCenter()
    ws_center = NSWorkspace.sharedWorkspace().notificationCenter()

    dist_center.addObserver_selector_name_object_(
        observer,
        "screenLocked:",
        "com.apple.screenIsLocked",
        None
    )
    dist_center.addObserver_selector_name_object_(
        observer,
        "screenUnlocked:",
        "com.apple.screenIsUnlocked",
        None
    )

    ws_center.addObserver_selector_name_object_(
        observer,
        "sleepNotification:",
        "NSWorkspaceWillSleepNotification",
        None
    )
    ws_center.addObserver_selector_name_object_(
        observer,
        "wakeNotification:",
        "NSWorkspaceDidWakeNotification",
        None
    )

    ws_center.addObserver_selector_name_object_(
        observer,
        "sleepNotification:",
        "NSWorkspaceScreensDidSleepNotification",
        None
    )
    ws_center.addObserver_selector_name_object_(
        observer,
        "wakeNotification:",
        "NSWorkspaceScreensDidWakeNotification",
        None
    )

    return observer, dist_center, ws_center
