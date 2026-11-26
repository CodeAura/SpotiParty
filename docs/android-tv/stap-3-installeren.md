---
description: Verbinding maken met de tv en beide apps installeren.
icon: download
---

# Stap 3: Installeren met ADB

Met **ADB** zet je de gebouwde apps vanaf je PC op de tv. ADB zit in de _platform-tools_ van de Android SDK. Werkt het commando `adb` niet in je terminal, voeg dan de map `platform-tools` toe aan je `PATH`, of start `adb` met het volledige pad.

{% stepper %}
{% step %}
### Verbinding maken

Voer dit uit in de map `SpotiParty`, met het IP-adres van je tv uit [stap 1](stap-1-debuggen.md):

```bash
adb connect 192.168.1.50
```

Op de tv verschijnt **"USB-foutopsporing toestaan?"**. Vink eventueel **Altijd toestaan vanaf deze computer** aan en kies **Toestaan**.

Controleer de verbinding met `adb devices`. Je tv staat in de lijst met de status `device`.
{% endstep %}

{% step %}
### SpotiParty installeren

```bash
adb install -r android/spotiparty/app/build/outputs/apk/release/app-release.apk
```

Je ziet `Success` als het gelukt is. De `-r` zorgt ervoor dat een oudere versie gewoon wordt vervangen.
{% endstep %}

{% step %}
### De oude Lyrics-app

Had je de **Lyrics**-app van een oudere versie? Die is niet meer nodig:

```bash
adb uninstall io.github.cleanyourtv.lyrics
```
{% endstep %}
{% endstepper %}

## Foutmeldingen

| Melding                                    | Wat het betekent                                                                                            | Oplossing                                                                                               |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `failed to connect` / `connection refused` | De tv is niet bereikbaar of foutopsporing staat uit                                                         | Controleer het IP-adres en of foutopsporing aan staat. Zitten PC en tv op hetzelfde netwerk?            |
| `unauthorized` bij `adb devices`           | Je hebt nog geen toestemming gegeven op de tv                                                               | Kijk op de tv en kies **Toestaan**. Geen melding? Doe `adb disconnect` en daarna opnieuw `adb connect`. |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE`       | Er staat al een versie op die met een andere sleutel is ondertekend (bijvoorbeeld gebouwd op een andere PC) | Verwijder de oude app eerst, zie [Updaten en verwijderen](updaten-en-verwijderen.md).                   |
| `more than one device/emulator`            | Er zijn meerdere apparaten verbonden                                                                        | Voeg `-s 192.168.1.50:5555` toe na `adb`.                                                               |

Volgende: [Stap 4: Toegang geven](stap-4-toegang-geven.md).
