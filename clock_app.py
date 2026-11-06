import os
import subprocess
from datetime import datetime
import rumps

from clocker import (
    start_session,
    stop_session,
    get_log_filepath,
    read_history,
    calculate_totals,
    format_duration,
    get_report_directory,
    choose_report_directory_dialog,
    setup_observers
)


class ClockerApp(rumps.App):
    def __init__(self):
        super(ClockerApp, self).__init__("Clocker", icon=None)
        
        self.title = "⏱️ --:--"
        self.today_item = rumps.MenuItem("Today: 00h 00m")
        self.week_item = rumps.MenuItem("This week: 00h 00m")
        
        self.menu = [
            self.today_item,
            self.week_item,
            None,
            rumps.MenuItem("Open Reports Folder", callback=self.open_reports),
            rumps.MenuItem("Change Reports Location...", callback=self.change_folder),
            None,
            rumps.MenuItem("Quit Clocker", callback=self.quit_app)
        ]

        # Register macOS sleep, wake, and lock listeners
        self.monitor, self.dist_center, self.ws_center = setup_observers()
        start_session()

    @rumps.timer(5)
    def update_ticker(self, _):
        now = datetime.now()
        filepath = get_log_filepath(now)
        sessions = read_history(filepath)
        day_total, week_total = calculate_totals(sessions, now)

        day_human = format_duration(day_total * 60)
        week_human = format_duration(week_total * 60)

        # Compact display in the macOS menu bar (e.g., ⏱️ 03h 45m)
        short_day = day_human.rsplit("m", 1)[0] + "m" if "m" in day_human else day_human
        self.title = f"⏱️ {short_day}"
        self.today_item.title = f"Today: {day_human}"
        self.week_item.title = f"This week: {week_human}"

    def open_reports(self, _):
        folder = get_report_directory()
        subprocess.run(["open", folder])

    def change_folder(self, _):
        new_path = choose_report_directory_dialog()
        if new_path:
            rumps.notification(
                title="Clocker",
                subtitle="Location Updated",
                message=f"Reports: {os.path.basename(new_path)}"
            )

    def quit_app(self, _):
        stop_session("Quit requested from menu bar")
        rumps.quit_application()


if __name__ == "__main__":
    ClockerApp().run()
