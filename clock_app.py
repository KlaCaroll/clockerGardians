import os
import subprocess
from datetime import datetime
import objc

from Foundation import NSObject, NSTimer
from AppKit import (
    NSApplication,
    NSApp,
    NSStatusBar,
    NSMenu,
    NSMenuItem,
    NSVariableStatusItemLength
)

from clocker import (
    start_session,
    stop_session,
    save_current_state,
    get_log_filepath,
    read_history,
    calculate_totals,
    format_duration,
    get_report_directory,
    choose_report_directory_dialog,
    setup_observers
)


class ClockerMenuApp(NSObject):
    def init(self):
        self = objc.super(ClockerMenuApp, self).init()
        if self is None:
            return None

        # Status Bar item
        self.status_bar = NSStatusBar.systemStatusBar()
        self.status_item = self.status_bar.statusItemWithLength_(NSVariableStatusItemLength)
        
        self.button = self.status_item.button()
        if self.button:
            self.button.setTitle_("⏱️ 00h 00m")

        # Native Dropdown Menu
        self.menu = NSMenu.alloc().init()

        self.today_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Today: 00h 00m", None, ""
        )
        self.week_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "This week: 00h 00m", None, ""
        )

        sync_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Save / Sync Now", "syncNow:", "s"
        )
        sync_item.setTarget_(self)

        open_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Open Reports Folder", "openReports:", ""
        )
        open_item.setTarget_(self)

        change_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Change Reports Location...", "changeLocation:", ""
        )
        change_item.setTarget_(self)

        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit Clocker", "quitApp:", "q"
        )
        quit_item.setTarget_(self)

        # Assemble menu
        self.menu.addItem_(self.today_item)
        self.menu.addItem_(self.week_item)
        self.menu.addItem_(NSMenuItem.separatorItem())
        self.menu.addItem_(sync_item)
        self.menu.addItem_(open_item)
        self.menu.addItem_(change_item)
        self.menu.addItem_(NSMenuItem.separatorItem())
        self.menu.addItem_(quit_item)

        self.status_item.setMenu_(self.menu)

        # System observers
        self.monitor, self.dist_center, self.ws_center = setup_observers()
        start_session()

        # Refresh timer (every 5 seconds)
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            5.0, self, "updateTicker:", None, True
        )

        self.refresh_display()
        return self

    def refresh_display(self):
        now = datetime.now()
        filepath = get_log_filepath(now)
        sessions = read_history(filepath)
        day_total, week_total = calculate_totals(sessions, now)

        day_human = format_duration(day_total * 60)
        week_human = format_duration(week_total * 60)

        short_day = day_human.rsplit("m", 1)[0] + "m" if "m" in day_human else day_human

        if self.button:
            self.button.setTitle_(f"⏱️ {short_day}")

        self.today_item.setTitle_(f"Today: {day_human}")
        self.week_item.setTitle_(f"This week: {week_human}")

    @objc.IBAction
    def updateTicker_(self, timer):
        self.refresh_display()

    @objc.IBAction
    def syncNow_(self, sender):
        save_current_state()
        self.refresh_display()

    @objc.IBAction
    def openReports_(self, sender):
        folder = get_report_directory()
        subprocess.run(["open", folder])

    @objc.IBAction
    def changeLocation_(self, sender):
        choose_report_directory_dialog()
        self.refresh_display()

    @objc.IBAction
    def quitApp_(self, sender):
        stop_session("Quit requested from menu bar")
        NSApp().terminate_(self)


def main():
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(1)
    delegate = ClockerMenuApp.alloc().init()
    app.setDelegate_(delegate)
    app.run()


if __name__ == "__main__":
    main()
