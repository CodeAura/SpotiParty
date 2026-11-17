---
description: SpotiParty installeren in Home Assistant, via HACS of met de hand.
icon: download
---

# Installeren

SpotiParty is voor Home Assistant **één bestand**: `spotiparty-card.js`. Het hele scherm zit erin. Je installeert het via HACS (aanbevolen) of zet het zelf neer.

{% tabs %}
{% tab title="Via HACS (aanbevolen)" %}
Klik op de knop: je eigen Home Assistant opent, en HACS voegt SpotiParty toe.

[![Open je Home Assistant en voeg SpotiParty toe aan HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=CodeAura\&repository=SpotiParty\&category=plugin)

1. Klik op de knop, controleer het adres van je Home Assistant en klik **Open link**.
2. Klik in HACS op **Downloaden**. HACS zet de kaart er vanzelf bij als bron.
3. Herlaad de browser met **Ctrl+F5** (Mac: **Cmd+Shift+R**).

**Werkt de knop niet?** Ga naar **HACS → ⋮ → Aangepaste repositories**, plak `https://github.com/CodeAura/SpotiParty`, kies type **Dashboard** en klik **Toevoegen**. Zoek daarna **SpotiParty** en klik **Downloaden**.
{% endtab %}

{% tab title="Met de hand" %}
1. Download **`spotiparty-card.js`** bij de [nieuwste release](https://github.com/CodeAura/SpotiParty/releases/latest).
2. Zet het in **`/config/www/spotiparty/`**. Dat kan met de add-on **File editor** (upload-icoon), **Studio Code Server** (slepen) of **Samba share** (netwerkmap `\\homeassistant.local\config`).
3. Ga naar **Instellingen → Dashboards → ⋮ → Bronnen** en voeg toe:
   * URL: `/local/spotiparty/spotiparty-card.js`
   * Type: **JavaScript-module**
4. Herlaad de browser met **Ctrl+F5**.

{% hint style="warning" %}
**Bestond de map `www` nog niet?** Herstart Home Assistant dan één keer (**Instellingen → Systeem → Herstarten**). Home Assistant kijkt alleen bij het opstarten of die map er is.
{% endhint %}
{% endtab %}
{% endtabs %}

{% hint style="info" %}
**Had je SpotiParty eerder met de hand geïnstalleerd** (met `index.html`, `party.js` enzovoort)? Gebruik je nu HACS, verwijder dan de oude bron `/local/spotiparty/…` bij **Bronnen**, zodat er geen twee versies tegelijk laden. De oude losse bestanden mogen weg.
{% endhint %}

Volgende: [Kaart toevoegen](kaart-toevoegen.md).
