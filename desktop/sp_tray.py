"""SpotiParty in the menu bar (macOS) or the notification area next to the clock (Windows).

    tray = sp_tray.start(root, icon_dir, items)     # None when this platform or build has no tray
    tray.update(items)                              # a new menu (only redrawn when it changed)
    tray.stop()

items: a list of (label, callback, enabled); None is a separator. Callbacks always run on Tk's thread (root.after),
so they may touch the window. on_click (Windows): what a click on the icon itself does.

macOS: an NSStatusItem through PyObjC, made on the main thread; Tk's Cocoa event loop delivers its clicks, so no
second loop is needed. Windows: pystray in a thread of its own. Without PyObjC / pystray there is simply no icon.
"""
import platform
import threading

MAC = platform.system() == "Darwin"
WINDOWS = platform.system() == "Windows"


def start(root, icon_dir, items, title="SpotiParty", on_click=None):
    try:
        if MAC:
            return _MacTray(root, icon_dir, items, title)
        if WINDOWS:
            return _WinTray(root, icon_dir, items, title, on_click)
    except Exception as e:  # noqa: BLE001  (a missing library or an odd desktop: SpotiParty works without the icon)
        print("SpotiParty: geen pictogram in de taakbalk:", e)
    return None


def _key(items):
    return [None if i is None else (i[0], bool(i[2])) for i in items]


# ---------- macOS ----------
if MAC:
    try:
        import objc
        from AppKit import NSApp, NSImage, NSMenu, NSMenuItem, NSStatusBar, NSVariableStatusItemLength
        from Foundation import NSObject

        class SpotiPartyTrayTarget(NSObject):
            """Receives the menu's clicks (Cocoa calls act: with the menu item)."""

            def initWithCallback_(self, cb):
                self = objc.super(SpotiPartyTrayTarget, self).init()
                if self is not None:
                    self.cb = cb
                return self

            def act_(self, sender):
                self.cb(int(sender.tag()))
    except ImportError:   # PyObjC not installed: start() reports it
        pass


class _MacTray:
    def __init__(self, root, icon_dir, items, title):
        self.root = root
        self.callbacks = []
        self.target = SpotiPartyTrayTarget.alloc().initWithCallback_(self._clicked)
        self.item = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
        image = NSImage.alloc().initWithContentsOfFile_(str(icon_dir / "tray-mac.png"))
        if image is not None:
            image.setSize_((18, 18))
            image.setTemplate_(True)      # black and white like the other menu bar icons, in light and dark mode
            self.item.button().setImage_(image)
        else:
            self.item.button().setTitle_("SP")
        self.item.button().setToolTip_(title)
        self.shown = None
        self.update(items)

    def _clicked(self, i):
        NSApp.activateIgnoringOtherApps_(True)   # a menu bar click doesn't bring the app forward by itself
        if 0 <= i < len(self.callbacks) and self.callbacks[i]:
            self.root.after(0, self.callbacks[i])

    def update(self, items):
        if _key(items) == self.shown:
            return
        self.shown = _key(items)
        menu = NSMenu.alloc().init()
        menu.setAutoenablesItems_(False)
        self.callbacks = []
        for it in items:
            if it is None:
                menu.addItem_(NSMenuItem.separatorItem())
                continue
            label, cb, enabled = it
            mi = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(label, "act:" if cb else None, "")
            mi.setTarget_(self.target)
            mi.setTag_(len(self.callbacks))
            mi.setEnabled_(bool(enabled and cb))
            self.callbacks.append(cb)
            menu.addItem_(mi)
        self.item.setMenu_(menu)

    def stop(self):
        NSStatusBar.systemStatusBar().removeStatusItem_(self.item)


# ---------- Windows ----------
class _WinTray:
    def __init__(self, root, icon_dir, items, title, on_click):
        import pystray
        from PIL import Image
        self.pystray, self.root = pystray, root
        self.on_click = on_click
        self.shown = None
        self.icon = pystray.Icon("SpotiParty", Image.open(icon_dir / "tray-windows.png"), title,
                                 menu=self._menu(items))
        self.shown = _key(items)
        threading.Thread(target=self.icon.run, daemon=True, name="tray").start()

    def _menu(self, items):
        p = self.pystray
        out = []
        if self.on_click:   # a click on the icon itself (not the menu): the default item, hidden
            out.append(p.MenuItem("SpotiParty", self._later(self.on_click), default=True, visible=False))
        for it in items:
            if it is None:
                out.append(p.Menu.SEPARATOR)
                continue
            label, cb, enabled = it
            action = self._later(cb) if cb else (lambda icon, item: None)
            out.append(p.MenuItem(label, action, enabled=bool(enabled and cb)))
        return p.Menu(*out)

    def _later(self, cb):
        return lambda icon, item: self.root.after(0, cb)   # pystray calls from its own thread: hand it to Tk

    def update(self, items):
        if _key(items) == self.shown:
            return
        self.shown = _key(items)
        self.icon.menu = self._menu(items)
        self.icon.update_menu()

    def stop(self):
        self.icon.stop()
