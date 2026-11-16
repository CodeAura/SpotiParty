---
description: De map web/ in /config/www/spotiparty/ zetten.
icon: folder-open
---

# Bestanden kopiëren

Home Assistant serveert alles wat in de map `/config/www/` staat op het adres `/local/`. Daar zet je SpotiParty neer.

## 1. Haal de bestanden op

Download SpotiParty als ZIP: open [github.com/CodeAura/SpotiParty](https://github.com/CodeAura/SpotiParty), klik op **Code → Download ZIP** en pak het uit. Je hebt alleen de map **`web/`** nodig.

## 2. Kopieer de inhoud naar Home Assistant

Kopieer de **inhoud** van `web/` naar `/config/www/spotiparty/`. Daarna ziet het er zo uit:

```
/config/www/spotiparty/
├── index.html
├── party.js
├── qr.js
├── serve.py      (niet nodig, mag blijven staan)
├── start.cmd     (niet nodig, mag blijven staan)
└── README.md     (niet nodig, mag blijven staan)
```

{% tabs %}
{% tab title="Samba share" %}
1. Installeer en start de add-on **Samba share** en stel een gebruikersnaam en wachtwoord in.
2. Open op je PC de netwerkmap `\\homeassistant.local\config` (Windows) of `smb://homeassistant.local/config` (Mac: **Finder → Ga → Verbind met server**).
3. Maak de map `www` aan als die nog niet bestaat, en daarin de map `spotiparty`.
4. Sleep de bestanden uit `web/` naar `www/spotiparty`.
{% endtab %}

{% tab title="File editor" %}
1. Installeer en open de add-on **File editor**.
2. Klik op het mapicoon, ga naar `/config/www` (maak die aan als hij er niet is) en maak de map `spotiparty`.
3. Gebruik het **upload**-icoon om `index.html`, `party.js` en `qr.js` één voor één te uploaden.
{% endtab %}

{% tab title="Studio Code Server" %}
1. Installeer en open de add-on **Studio Code Server**.
2. Maak in de verkenner de map `www/spotiparty` aan.
3. Sleep de bestanden uit `web/` naar die map.
{% endtab %}
{% endtabs %}

{% hint style="warning" %}
**Bestond de map `www` nog niet?** Herstart Home Assistant dan één keer (**Instellingen → Systeem → Herstarten**). Home Assistant kijkt alleen bij het opstarten of die map er is.
{% endhint %}

## 3. Controleer of het werkt

Open in je browser:

```
http://homeassistant.local:8123/local/spotiparty/index.html
```

Gebruik je een ander adres voor Home Assistant, vervang dan het begin. Zie je SpotiParty, dan staat alles goed.

{% hint style="info" %}
Bestanden in `/config/www` zijn bereikbaar zonder in te loggen. Dat is hier geen probleem: de SpotiParty-bestanden bevatten geen persoonlijke gegevens. Je login en instellingen staan alleen in de browser die het dashboard toont.
{% endhint %}

Volgende: [Kaart toevoegen](kaart-toevoegen.md).
