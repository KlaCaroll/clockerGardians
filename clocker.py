import time
import os
import re
import json
import atexit
import signal
from datetime import datetime
from itertools import groupby

from Foundation import (
    NSObject,
    NSDistributedNotificationCenter,
    NSRunLoop,
    NSDate,
    NSDefaultRunLoopMode
)
from AppKit import (
    NSWorkspace,
    NSWorkspaceWillSleepNotification,
    NSWorkspaceDidWakeNotification,
    NSWorkspaceScreensDidSleepNotification,
    NSWorkspaceScreensDidWakeNotification,
    NSOpenPanel,
    NSApplication,
    NSModalResponseOK
)

# CONFIGURATION
MIN_SESSION_SECONDS = 5
TICKER_INTERVAL = 5

active_start = None
active_start_datetime = None
session_active = False
loop_count = 0


# LOGS
def log_debug(message):
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] 🔍 {message}", flush=True)


# FORMATAGE DES DURÉES
def format_duration(seconds):
    total_seconds = max(0, int(round(seconds)))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}h {minutes:02d}m {secs:02d}s"


# GESTION DES DOSSIERS ET CONFIGURATION
def get_config_filepath():
    app_support = os.path.expanduser("~/Library/Application Support/Clocker")
    os.makedirs(app_support, exist_ok=True)
    return os.path.join(app_support, "config.json")


def load_custom_report_directory():
    config_file = get_config_filepath()
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                custom_dir = data.get("report_directory")
                if custom_dir and os.path.isdir(custom_dir):
                    return custom_dir
        except Exception:
            pass
    return None


def save_custom_report_directory(chosen_path):
    config_file = get_config_filepath()
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({"report_directory": chosen_path}, f, indent=2)
    except Exception as e:
        log_debug(f"Configuration save error: {e}")


def choose_report_directory_dialog():
    NSApplication.sharedApplication()
    panel = NSOpenPanel.openPanel()
    panel.setTitle_("Choisir l'emplacement des rapports Clocker")
    panel.setMessage_("Sélectionnez le dossier où enregistrer vos rapports :")
    panel.setCanChooseFiles_(False)
    panel.setCanChooseDirectories_(True)
    panel.setAllowsMultipleSelection_(False)
    panel.setCanCreateDirectories_(True)

    if panel.runModal() == NSModalResponseOK:
        urls = panel.URLs()
        if urls:
            selected_path = str(urls[0].path())
            save_custom_report_directory(selected_path)
            return selected_path
    return None


def get_report_directory():
    custom_dir = load_custom_report_directory()
    if custom_dir:
        os.makedirs(custom_dir, exist_ok=True)
        return custom_dir

    default_dir = os.path.expanduser("~/Documents/Clocker/rapport")
    os.makedirs(default_dir, exist_ok=True)
    return default_dir


def get_log_filepath(reference_datetime=None):
    if reference_datetime is None:
        reference_datetime = datetime.now()

    iso_year, iso_week, _ = reference_datetime.isocalendar()
    filename = f"rapport_temps_semaine_{iso_week:02d}_{iso_year}.txt"
    return os.path.join(get_report_directory(), filename)


# LECTURE ET CALCULS
def read_history(filepath):
    sessions = []
    if not os.path.exists(filepath):
        return sessions

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if "SESSION" not in line:
                    continue
                try:
                    date_match = re.search(
                        r"(\d{4}-\d{2}-\d{2})(?:\s+(\d{1,2}):(\d{2}):(\d{2})|\s+(\d{1,2})h(\d{2}))?",
                        line
                    )
                    if not date_match:
                        continue

                    date_str = date_match.group(1)
                    hour_sec = date_match.group(2)
                    min_sec = date_match.group(3)
                    sec = date_match.group(4)
                    hour_min = date_match.group(5)
                    min_leg = date_match.group(6)

                    if hour_sec is not None:
                        session_datetime = datetime.strptime(
                            f"{date_str} {hour_sec.zfill(2)}:{min_sec}:{sec}",
                            "%Y-%m-%d %H:%M:%S"
                        )
                    elif hour_min is not None:
                        session_datetime = datetime.strptime(
                            f"{date_str} {hour_min.zfill(2)}h{min_leg}",
                            "%Y-%m-%d %Hh%M"
                        )
                    else:
                        session_datetime = datetime.strptime(date_str, "%Y-%m-%d")

                    minutes_match = re.search(
                        r"SESSION\s*\|?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:min|minutes)\b",
                        line,
                        re.IGNORECASE
                    )
                    if not minutes_match:
                        continue

                    minutes = float(minutes_match.group(1))
                    if minutes >= 0:
                        sessions.append({"datetime": session_datetime, "minutes": minutes})
                except (ValueError, IndexError):
                    continue
    except Exception as e:
        log_debug(f"History reading error: {e}")

    return sessions


def calculate_totals(sessions, reference_datetime):
    target_date = reference_datetime.date()
    iso_year, iso_week, _ = reference_datetime.isocalendar()

    day_total = 0.0
    week_total = 0.0

    for session in sessions:
        session_datetime = session["datetime"]
        session_date = session_datetime.date()
        session_iso_year, session_iso_week, _ = session_datetime.isocalendar()

        if session_date == target_date:
            day_total += session["minutes"]

        if session_iso_year == iso_year and session_iso_week == iso_week:
            week_total += session["minutes"]

    return day_total, week_total


# ÉCRITURE DU RAPPORT
def update_log(session_duration, start_datetime, end_time):
    temp_filepath = None
    try:
        if session_duration <= 0:
            return

        session_minutes = round(session_duration / 60, 6)
        session_human = format_duration(session_duration)
        filepath = get_log_filepath(start_datetime)

        log_debug(
            f"Saving session: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')} "
            f"to {end_time.strftime('%H:%M:%S')} | {session_human}"
        )

        sessions = read_history(filepath)
        sessions.append({"datetime": start_datetime, "minutes": session_minutes})

        day_total, week_total = calculate_totals(sessions, start_datetime)
        day_human = format_duration(day_total * 60)
        week_human = format_duration(week_total * 60)

        iso_year, iso_week, _ = start_datetime.isocalendar()
        weekly_sessions = [
            s for s in sessions
            if s["datetime"].isocalendar()[0] == iso_year
            and s["datetime"].isocalendar()[1] == iso_week
        ]
        weekly_sessions.sort(key=lambda s: s["datetime"], reverse=True)

        disclaimer = (
            "NOTE :\n"
            "Le compteur se basant sur l'ecran deverouille, toute coupure pour aller chercher de l'eau,\n"
            "aller au toilettes ou se deplacer dans l'open space n'est pas comptabilise.\n"
            "Il en va de meme pour les 15min de pause autorisees par la loi.\n"
            "Ce compteur total sous-estime donc le vrai total des heures de travail.\n"
        )

        temp_filepath = filepath + ".tmp"
        with open(temp_filepath, "w", encoding="utf-8") as f:
            f.write("=" * 50 + "\n")
            f.write(f" TIME REPORT AT : {end_time.strftime('%d/%m/%Y at %H:%M:%S')}\n")
            f.write(f" ISO WEEK : {iso_week:02d} / {iso_year}\n")
            f.write(f" TOTAL TODAY : {day_human}\n")
            f.write(f" TOTAL WEEK : {week_human}\n")
            f.write("=" * 50 + "\n\n")

            f.write(disclaimer + "\n")
            f.write("DETAILS :\n")

            for day_date, group in groupby(weekly_sessions, key=lambda s: s["datetime"].date()):
                day_sessions = list(group)
                day_subtotal = sum(s["minutes"] for s in day_sessions)
                day_subtotal_human = format_duration(day_subtotal * 60)

                f.write(f"\n--- {day_date.strftime('%Y-%m-%d')} (Total: {day_subtotal_human}) ---\n")

                for s in day_sessions:
                    s_start = s["datetime"]
                    mins = s["minutes"]
                    dur = format_duration(mins * 60)
                    f.write(
                        f"  {s_start.strftime('%Y-%m-%d %H:%M:%S')} "
                        f"| DURATION : {dur} | SESSION {mins:.6f} min\n"
                    )

        os.replace(temp_filepath, filepath)
        log_debug("Report saved successfully.")
    except Exception as e:
        log_debug(f"Writing error: {e}")
        if temp_filepath and os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except OSError:
                pass


# CYCLE DE VIE DE SESSION
def start_session():
    global active_start, active_start_datetime, session_active
    if session_active:
        return
    active_start = time.monotonic()
    active_start_datetime = datetime.now()
    session_active = True
    log_debug(f"SESSION STARTED: {active_start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")


def stop_session(reason="Stop"):
    global active_start, active_start_datetime, session_active
    if not session_active or active_start is None:
        return

    end_time = datetime.now()
    duration = time.monotonic() - active_start
    log_debug(f"{reason} | Duration: {format_duration(duration)}")

    if duration >= MIN_SESSION_SECONDS:
        update_log(duration, active_start_datetime, end_time)

    active_start = None
    active_start_datetime = None
    session_active = False


# NOTIFICATIONS SYSTÈME MACOS
class ActivityMonitor(NSObject):
    def screenLocked_(self, n):
        log_debug("NOTIFICATION: SCREEN LOCK")
        stop_session("Screen locked")

    def screenUnlocked_(self, n):
        log_debug("NOTIFICATION: SCREEN UNLOCK")
        start_session()

    def systemWillSleep_(self, n):
        log_debug("NOTIFICATION: SYSTEM SLEEP")
        stop_session("System sleep")

    def systemDidWake_(self, n):
        log_debug("NOTIFICATION: SYSTEM WAKE")
        start_session()

    def screensDidSleep_(self, n):
        log_debug("NOTIFICATION: DISPLAY SLEEP")
        stop_session("Display sleep")

    def screensDidWake_(self, n):
        log_debug("NOTIFICATION: DISPLAY WAKE")
        start_session()


def setup_observers():
    monitor = ActivityMonitor.alloc().init()
    dist = NSDistributedNotificationCenter.defaultCenter()
    dist.addObserver_selector_name_object_(monitor, "screenLocked:", "com.apple.screenIsLocked", None)
    dist.addObserver_selector_name_object_(monitor, "screenUnlocked:", "com.apple.screenIsUnlocked", None)

    ws = NSWorkspace.sharedWorkspace().notificationCenter()
    ws.addObserver_selector_name_object_(monitor, "systemWillSleep:", NSWorkspaceWillSleepNotification, None)
    ws.addObserver_selector_name_object_(monitor, "systemDidWake:", NSWorkspaceDidWakeNotification, None)
    ws.addObserver_selector_name_object_(monitor, "screensDidSleep:", NSWorkspaceScreensDidSleepNotification, None)
    ws.addObserver_selector_name_object_(monitor, "screensDidWake:", NSWorkspaceScreensDidWakeNotification, None)
    return monitor, dist, ws


def handle_exit_signal(signum, frame):
    stop_session("Terminal closed or signal received")
    raise SystemExit(0)

signal.signal(signal.SIGHUP, handle_exit_signal)
signal.signal(signal.SIGTERM, handle_exit_signal)
atexit.register(stop_session, reason="Script termination")


def main():
    global loop_count
    print("CLOCKED - MONITORING ACTIF")
    monitor, dist, ws = setup_observers()
    start_session()

    try:
        while True:
            NSRunLoop.currentRunLoop().runMode_beforeDate_(
                NSDefaultRunLoopMode,
                NSDate.dateWithTimeIntervalSinceNow_(1.0)
            )
            loop_count += 1
    except KeyboardInterrupt:
        print()
        stop_session("Arrêt manuel (CTRL+C)")
    finally:
        dist.removeObserver_(monitor)
        ws.removeObserver_(monitor)

if __name__ == "__main__":
    main()