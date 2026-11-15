# SpotiParty

The song that's playing, full screen: the cover blurred behind everything, the lyrics running along with the
song, what comes next in the queue, and a QR code that lets your friends join your Spotify Jam and add their
own songs.

SpotiParty runs in three places:

| Where | Folder | What it is |
|---|---|---|
| **Browser: PC or Home Assistant dashboard** | [`web/`](web/) | One static page, no build step and no libraries. Shows your Spotify account or any Home Assistant media player. |
| **Android TV / Google TV** | [`android/party-mode/`](android/party-mode/) | A TV app that shows what plays on the TV, with a page on your phone to set the Jam link. |
| **Lyrics for the TV** | [`android/lyrics/`](android/lyrics/) | A small helper app with no screen that looks up lyrics for the TV app. |

Lyrics come from [lrclib.net](https://lrclib.net) (free, no account). SpotiParty only reads from Spotify
(what plays, the queue) and never controls playback. Logins and settings stay on your own device.

## Web: PC and Home Assistant

```bash
python web/serve.py
```

On Windows, double-click `web/start.cmd`. Setup, the Home Assistant card and the URL options are in
[`web/README.md`](web/README.md).

## Android TV

You need JDK 17 and the Android SDK (platform 34). Build both apps and install them over ADB:

```bash
cd android/party-mode && ./gradlew assembleRelease && cd ../..
cd android/lyrics && ./gradlew assembleRelease && cd ../..
adb install -r android/party-mode/app/build/outputs/apk/release/app-release.apk
adb install -r android/lyrics/app/build/outputs/apk/release/app-release.apk
```

Then give the TV app access, either in the TV's settings or over ADB:

```bash
adb shell cmd notification allow_listener io.github.cleanyourtv.partymode/io.github.cleanyourtv.partymode.PartyListener
adb shell appops set io.github.cleanyourtv.partymode SYSTEM_ALERT_WINDOW allow
```

Each command does one thing:
- **`allow_listener`** lets the app see the song that's playing. That's Notification access; the app reads no notifications.
- **`appops set`** lets the app open by itself when Spotify starts playing ("Display over other apps"). It's optional.

To read the lyrics, the TV app and the Lyrics app have to be signed with the same key. Build both on the same machine.

Open SpotiParty on the TV and scan the code in the corner with your phone to set the Jam link. **Menu** on the remote
shows that code again.

The package names (`io.github.cleanyourtv.*`) are kept as they are. That way both apps still work as cards and as
the *Now playing* lyrics in the [CleanYourTV](https://github.com/Gathin23/cleanyourtv) launcher, where SpotiParty
started out as an add-on.

## Licence

MIT, see [LICENSE](LICENSE).
