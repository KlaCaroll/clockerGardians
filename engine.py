import os
import json
import logging
from datetime import datetime

logger = logging.getLogger("clocker")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


class TimeTrackerEngine:
    def __init__(self):
        self.active_session_start = None
        self.active_lock_start = None

    def get_config_directory(self):
        app_support = os.path.expanduser("~/Library/Application Support/Clocker")
        os.makedirs(app_support, exist_ok=True)
        return app_support

    def get_config_filepath(self):
        return os.path.join(self.get_config_directory(), "config.json")

    def save_custom_report_directory(self, chosen_path):
        config_file = self.get_config_filepath()
        try:
            clean_path = str(chosen_path).strip()
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump({"report_directory": clean_path}, f, indent=2)
            logger.info(f"Report directory updated to: {clean_path}")
        except Exception as e:
            logger.error(f"Configuration save error: {e}")

    def get_report_directory(self):
        config_file = self.get_config_filepath()
        target_dir = None

        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    target_dir = data.get("report_directory")
            except Exception as e:
                logger.error(f"Error reading configuration: {e}")

        if not target_dir or not os.path.exists(target_dir):
            target_dir = os.path.expanduser("~/Documents")

        reports_folder = os.path.join(target_dir, "Clocker_Reports")
        os.makedirs(reports_folder, exist_ok=True)
        return reports_folder

    def get_report_filepath(self, date_obj):
        reports_dir = self.get_report_directory()
        cal = date_obj.isocalendar()
        filename = f"rapport_temps_semaine_{cal[1]}_{cal[0]}.txt"
        return os.path.join(reports_dir, filename)

    @staticmethod
    def format_duration(seconds):
        total_seconds = max(0, int(seconds))
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        return f"{hours:02d}h {minutes:02d}m {secs:02d}s"

    @staticmethod
    def format_display_duration(seconds):
        total_seconds = max(0, int(seconds))
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}h {minutes:02d}m"

    def read_report_sessions(self, filepath):
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

    def calculate_totals(self, sessions, now):
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

        if self.active_session_start is not None:
            elapsed = (now - self.active_session_start).total_seconds() / 60.0
            day_total += elapsed
            week_total += elapsed

        return day_total, week_total

    def get_current_totals(self):
        now = datetime.now()
        filepath = self.get_report_filepath(now)
        sessions = self.read_report_sessions(filepath)
        return self.calculate_totals(sessions, now)

    def write_weekly_report(self, filepath, sessions, now):
        header = (
            "================================================================================\n"
            "                                CLOCKER REPORT                                 \n"
            "================================================================================\n\n"
        )

        day_total, week_total = self.calculate_totals(sessions, now)
        gen_time = now.strftime("%Y-%m-%d %H:%M:%S")

        summary = (
            f"Generated at: {gen_time}\n"
            f"Today's Total:     {self.format_duration(day_total * 60)}\n"
            f"This Week's Total: {self.format_duration(week_total * 60)}\n\n"
            "--------------------------------------------------------------------------------\n"
            "NOTE:\n"
            "Because the tracker relies on screen unlock status, short breaks away from the desk\n"
            "(such as grabbing water, using the restroom, or walking across the office) are not deducted\n"
            "unless the screen is locked.\n"
            "Similarly, standard statutory breaks (e.g., 15-minute breaks) are not automatically factored in.\n"
            "As a result, this total may slightly underestimate or differ from your actual billable work hours.\n\n"
            "--------------------------------------------------------------------------------\n"
            "SESSION DETAILS\n"
            "--------------------------------------------------------------------------------\n"
        )

        body_lines = []
        for s in sessions:
            dur_str = self.format_duration(s["duration"] * 60)
            start_str = s["start"].strftime("%Y-%m-%d %H:%M:%S")
            end_str = s["end"].strftime("%Y-%m-%d %H:%M:%S")
            body_lines.append(f"[{start_str}] -> [{end_str}] | Active: {dur_str}")

        sessions_block = "\n".join(body_lines) if body_lines else "No recorded sessions yet."

        nb = (
            "\n\n--------------------------------------------------------------------------------\n"
            "N.B. (Nota Bene):\n"
            "For the most accurate records, remember to lock your screen (Cmd + Ctrl + Q) whenever you step away.\n"
        )

        content = header + summary + sessions_block + nb

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def start_session(self):
        if self.active_session_start is None:
            self.active_session_start = datetime.now()
            self.active_lock_start = None
            logger.info(f"Session started: {self.active_session_start.strftime("%Y-%m-%d %H:%M:%S")}")

    def stop_session(self, reason=""):
        if self.active_session_start is None:
            return

        now = datetime.now()
        filepath = self.get_report_filepath(now)
        duration_min = (now - self.active_session_start).total_seconds() / 60.0

        sessions = self.read_report_sessions(filepath)
        sessions.append({
            "start": self.active_session_start,
            "end": now,
            "duration": duration_min
        })

        self.write_weekly_report(filepath, sessions, now)
        logger.info(f"Session stopped: {reason} ({self.format_duration(duration_min * 60)})")
        self.active_session_start = None

    def save_current_state(self):
        now = datetime.now()
        filepath = self.get_report_filepath(now)
        self.stop_session("Manual sync requested")
        self.start_session()
        logger.info(f"Manual sync completed to: {filepath}")
        return filepath
