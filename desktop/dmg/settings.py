# dmgbuild settings for SpotiParty-macos-<arch>.dmg: the window you see when you open the download, with the app on
# the left, a shortcut to Apps on the right and an arrow between them. Used by desktop/build-macos.sh:
#
#   dmgbuild -s desktop/dmg/settings.py -D app=desktop/dist/SpotiParty.app -D bg=<background.tiff> SpotiParty out.dmg
#
# dmgbuild writes the window layout (.DS_Store) itself, so no Finder scripting and no permission prompts.
import os.path

app = defines.get("app", "desktop/dist/SpotiParty.app")  # noqa: F821 (dmgbuild provides `defines`)
appname = os.path.basename(app)

# The volume (what Finder shows in the sidebar while it is open) gets the app's icon.
import glob
_icns = sorted(glob.glob(os.path.join(app, "Contents", "Resources", "*.icns")))
icon = _icns[0] if _icns else None

# UDZO: zlib, readable on every macOS; the updater (desktop/sp_update.py) mounts it the same way.
format = "UDZO"
filesystem = "HFS+"

files = [app]
# Called "Apps", as the folder is called in Dutch macOS and on the background.
symlinks = {"Apps": "/Applications"}

# The picture behind the icons: a TIFF with the 1x and 2x versions (sharp on Retina). See make_background.py.
background = defines.get("bg", "desktop/dmg/background.png")  # noqa: F821

window_rect = ((200, 140), (640, 400))   # position, then size in points; matches make_background.py
default_view = "icon-view"
show_toolbar = False
show_tab_view = False
show_pathbar = False
show_sidebar = False
show_status_bar = False
include_icon_view_settings = True

arrange_by = None
icon_size = 112
text_size = 13
label_pos = "bottom"
icon_locations = {
    appname: (160, 178),
    "Apps": (480, 178),
}
hide_extension = [appname]
