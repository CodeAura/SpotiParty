---
description: SpotiParty als Webpagina-kaart in je dashboard zetten.
icon: table-cells-large
---

# Kaart toevoegen

{% stepper %}
{% step %}
### Open je dashboard in bewerkmodus

Open het dashboard waar SpotiParty moet komen en klik rechtsboven op het **potlood** (**Dashboard bewerken**).
{% endstep %}

{% step %}
### Voeg een Webpagina-kaart toe

Kies **+ Kaart toevoegen** en zoek de kaart **Webpagina** (_Webpage_).
{% endstep %}

{% step %}
### Vul het adres in

Vul als URL in:

```
/local/spotiparty/index.html?source=ha&entity=media_player.woonkamer
```

Vervang `media_player.woonkamer` door je eigen speler. De naam vind je onder **Instellingen → Apparaten en diensten → Entiteiten**.

Laat je `&entity=…` weg, dan kiest SpotiParty zelf: de speler die op dat moment speelt, en anders een speler die gepauzeerd is met een nummer.
{% endstep %}

{% step %}
### Opslaan

Klik op **Opslaan** en daarna op **Gereed**. Zet muziek aan en je ziet de hoes, de titel en de songtekst.
{% endstep %}
{% endstepper %}

## Liever YAML?

Kies bij de kaart **Code-editor weergeven** en plak:

```yaml
type: iframe
url: /local/spotiparty/index.html?source=ha&entity=media_player.woonkamer
aspect_ratio: 16:9
```

## Hoe ziet het eruit?

* **Brede kaart:** hoes links, songtekst in het midden, QR-code rechtsonder. Net als op de tv.
* **Smalle kaart:** SpotiParty zet alles vanzelf onder elkaar.

## De Jam-link instellen

Klik in de kaart en druk op **S**, of beweeg de muis en klik op **⚙**. Plak je Jam-link (zie [Een Spotify Jam starten](../aan-de-slag/spotify-jam.md)) en klik op **Op het scherm zetten**.

{% hint style="success" %}
**Geen token nodig.** Omdat de kaart door je eigen Home Assistant wordt geserveerd, gebruikt SpotiParty de login van je dashboard om de standen van je spelers te lezen.
{% endhint %}

Volgende: [Extra's: kiosk, Hierna en andere computers](extras.md).
