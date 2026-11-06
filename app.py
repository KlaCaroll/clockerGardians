import sys
import subprocess
import objc

from Foundation import (
    NSObject,
    NSDistributedNotificationCenter,
    NSTimer
)
from AppKit import (
    NSApplication,
    NSApp,
    NSStatusBar,
    NSVariableStatusItemLength,
    NSMenu,
    NSMenuItem,
    NSOpenPanel,
    NSModalResponseOK,
    NSWorkspace
)

import engine


class SystemEventsObserver(NSObject):
    def screenLocked_(self, notification):
        engine.stop_session("Screen locked")

    def screenUnlocked_(self, notification):
        engine.start_session()

    def sleepNotification_(self, notification):
        engine.stop_session("System sleep")

    def wakeNotification_(self, notification):
        engine.start_session()


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


class ClockerApp(NSObject):
    def init(self):
        self = objc.super(ClockerApp, self).init()
        if self is None:
            return None
        self.status_item = None
        self.today_item = None
        self.week_item = None
        self.observer_refs = None
        return self

    def build_menu(self):
        menu = NSMenu.alloc().init()

        self.today_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Today: 00h 00m", None, ""
        )
        self.today_item.setEnabled_(False)
        menu.addItem_(self.today_item)

        self.week_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "This week: 00h 00m", None, ""
        )
        self.week_item.setEnabled_(False)
        menu.addItem_(self.week_item)

        menu.addItem_(NSMenuItem.separatorItem())

        sync_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Save / Sync Now", "manualSync:", "s"
        )
        sync_item.setTarget_(self)
        menu.addItem_(sync_item)

        open_folder_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Open Reports Folder", "openFolder:", ""
        )
        open_folder_item.setTarget_(self)
        menu.addItem_(open_folder_item)

        change_loc_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Change Reports Location...", "changeLocation:", ""
        )
        change_loc_item.setTarget_(self)
        menu.addItem_(change_loc_item)

        menu.addItem_(NSMenuItem.separatorItem())

        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit Clocker", "quitApp:", "q"
        )
        quit_item.setTarget_(self)
        menu.addItem_(quit_item)

        return menu

    def applicationDidFinishLaunching_(self, notification):
        engine.start_session()
        self.observer_refs = setup_observers()

        status_bar = NSStatusBar.systemStatusBar()
        self.status_item = status_bar.statusItemWithLength_(NSVariableStatusItemLength)
        self.status_item.button().setTitle_("⏱️ 00h 00m")
        self.status_item.setMenu_(self.build_menu())

        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1.0, self, "updateTick:", None, True
        )
        self.updateTick_(None)

    def updateTick_(self, timer):
        day_total, week_total = engine.get_current_totals()
        display_text = f"⏱️ {engine.format_display_duration(day_total * 60)}"
        if self.status_item:
            self.status_item.button().setTitle_(display_text)
        if self.today_item:
            self.today_item.setTitle_(f"Today: {engine.format_display_duration(day_total * 60)}")
        if self.week_item:
            self.week_item.setTitle_(f"This week: {engine.format_display_duration(week_total * 60)}")

    def manualSync_(self, sender):
        engine.save_current_state()
        self.updateTick_(None)

    def openFolder_(self, sender):
        folder = engine.get_report_directory()
        subprocess.run(["open", folder])

    def changeLocation_(self, sender):
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
                engine.save_custom_report_directory(selected_path)
                engine.save_current_state()

    def quitApp_(self, sender):
        engine.stop_session("Application quit")
        NSApp().terminate_(self)


def main():
    app = NSApplication.sharedApplication()
    delegate = ClockerApp.alloc().init()
    app.setDelegate_(delegate)
    app.run()


if __name__ == "__main__":
    main()