// Party games (horizontal panels), where it works, the steps, prices, questions, the final call and the footer.
import { useRef, useState } from "react";
import { gsap, ScrollTrigger, useGSAP } from "../lib/motion.js";
import SpotlightCard from "../components/reactbits/SpotlightCard/SpotlightCard.jsx";
import TiltedCard from "../components/reactbits/TiltedCard/TiltedCard.jsx";
import CountUp from "../components/reactbits/CountUp/CountUp.jsx";
import SplitText from "../components/reactbits/SplitText/SplitText.jsx";
import Magnet from "../components/reactbits/Magnet/Magnet.jsx";
import Pic from "../components/Pic.jsx";
import { Tv, Laptop, Apple, Cpu, Server, House, MicVocal, Plus, Download, Vote, Crown } from "lucide-react";
import { useLatestRelease } from "../lib/latestRelease.js";

const PANELS = [
  { img: "games", tag: [Vote, "Stem het volgende nummer"], title: "De gasten kiezen wat er komt", phone: true,
    text: "Drie nummers uit je afspeellijst en 60 seconden om te stemmen. De winnaar gaat vanzelf in de wachtrij. Op de telefoon ook een eigen kaart voor muziekbingo." },
  { img: "quiz", tag: [MicVocal, "Raad het nummer"], title: "Wie raadt hem het snelst?",
    text: "Bij elk nieuw nummer blijven titel en hoes 15 seconden geheim. Gasten raden op hun telefoon: hoe sneller, hoe meer punten." },
  { img: "winner", tag: [Crown, "Stand van de avond"], title: "En de winnaar is…",
    text: "Quiz, bingo en stemmen tellen samen op. Aan het eind van het feest staat de winnaar groot op elk scherm." },
];

export function Party() {
  const root = useRef(null);
  useGSAP(() => {
    const mm = gsap.matchMedia();
    mm.add("(prefers-reduced-motion: no-preference)", () => {
      const track = root.current.querySelector(".party-track");
      const distance = () => Math.max(0, track.scrollWidth - window.innerWidth);
      const scroll = gsap.to(track, {
        x: () => -distance(), ease: "none",
        scrollTrigger: { trigger: ".party-pin", start: "top top", end: () => "+=" + distance(), pin: true, scrub: 1, invalidateOnRefresh: true },
      });
      gsap.utils.toArray(".panel").forEach((panel) => {
        gsap.from(panel.querySelector(".panel-text"), {
          y: 40, opacity: 0, duration: 0.8, ease: "power3.out",
          scrollTrigger: { trigger: panel, containerAnimation: scroll, start: "left 75%" },
        });
        const phone = panel.querySelector(".phone");
        if (phone) gsap.from(phone, { yPercent: 40, rotate: 8, opacity: 0, duration: 1, ease: "back.out(1.6)",
          scrollTrigger: { trigger: panel, containerAnimation: scroll, start: "left 60%" } });
      });
    });
  }, { scope: root });

  return (
    <section ref={root} id="feest" className="party">
      <div className="party-pin">
        <div className="wrap party-head">
          <span className="eyebrow">Feestspellen</span>
          <h2>Meer dan meezingen</h2>
          <p className="lead">Gasten spelen mee op hun telefoon: Raad het nummer, Muziekbingo en stemmen op het volgende nummer. Gratis, gewoon in de Hub.</p>
        </div>
        <div className="party-track">
          {PANELS.map((p) => (
            <article key={p.img} className="panel">
              <div className="panel-media">
                <Pic name={p.img} width="1600" height="900" alt={p.title} />
                {p.phone && <Pic name="guest" eager className="phone" width="780" height="2200" alt="De gastenpagina op een telefoon: je naam en punten, stemmen op het volgende nummer en je bingokaart" />}
              </div>
              <div className="panel-text">
                <span className="panel-tag">{(([Icon, text]) => <><Icon size={15} strokeWidth={2.25} aria-hidden="true" />{text}</>)(p.tag)}</span>
                <h3>{p.title}</h3>
                <p>{p.text}</p>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

const PLATFORMS = [
  [Tv, "Android TV & Google TV", "Hetzelfde scherm als op de pc, rechtstreeks van je Hub: elke update van de Hub staat meteen op de tv."],
  [Laptop, "Windows", "Installeren, dubbelklikken, klaar. Werkt zichzelf bij."],
  [Apple, "macOS", <>Voor Macs met Apple silicon en Intel, werkt zichzelf bij. <a href="https://github.com/CodeAura/SpotiParty/releases/latest">Download de .dmg</a>.</>],
  [Cpu, "Raspberry Pi", "Een vast feestscherm aan je tv of beamer, en als je wilt ook de Hub."],
  [Server, "Linux-server & Proxmox", <>De Hub zonder scherm, op je NAS of thuisserver: met systemd, Docker, of op Proxmox met <a href="https://spotiparty.gitbook.io/spotiparty/hub/proxmox">één commando</a>.</>],
  [House, "Home Assistant", "Als kaart via HACS, ook op je wandtablet. Werkt met Sonos, Cast en Music Assistant."],
];

export function Platforms() {
  const root = useRef(null);
  useGSAP(() => {
    const mm = gsap.matchMedia();
    mm.add("(prefers-reduced-motion: no-preference)", () => {
      gsap.from(".plist li", { x: -50, opacity: 0, duration: 0.8, ease: "power3.out", stagger: 0.08,
        scrollTrigger: { trigger: ".plist", start: "top 80%" } });
      gsap.from(".devices .laptop", { y: 90, opacity: 0, duration: 1.2, ease: "power3.out",
        scrollTrigger: { trigger: ".devices", start: "top 80%" } });
      gsap.fromTo(".devices .tablet", { y: 140 }, { y: -30, ease: "none",
        scrollTrigger: { trigger: ".devices", start: "top bottom", end: "bottom top", scrub: 1 } });
    });
  }, { scope: root });

  return (
    <section ref={root} id="overal">
      <div className="wrap platforms">
        <div>
          <span className="eyebrow">Waar het werkt</span>
          <h2>Op het scherm dat je al hebt</h2>
          <p className="lead" style={{ marginTop: 18 }}>Eén Hub, zoveel schermen als je wilt. Ze vinden elkaar vanzelf in je netwerk.</p>
          <ul className="plist">
            {PLATFORMS.map(([Icon, title, text]) => (
              <li key={title}><span className="icon" aria-hidden="true"><Icon size={26} strokeWidth={1.75} /></span><div><b>{title}</b><span>{text}</span></div></li>
            ))}
          </ul>
        </div>
        <div className="devices" aria-hidden="true">
          <div className="laptop"><div className="scr"><Pic name="screen" width="1600" height="900" alt="" /></div><div className="base" /></div>
          <div className="tablet">
            <TiltedCard imageSrc="/assets/card.jpg" altText="" captionText="Home Assistant · Woonkamer" containerHeight="100%"
              containerWidth="100%" imageHeight="100%" imageWidth="100%" rotateAmplitude={10} scaleOnHover={1.04}
              showTooltip={false} flipOnClick={false} radius={18} />
          </div>
        </div>
      </div>
    </section>
  );
}

const STEPS = [
  ["Installeer de Hub", "De Windows- of Mac-app, een Raspberry Pi, een Linux-server of Proxmox. Open het dashboard en kies je eigen PIN; een korte rondleiding doet de rest.", 5],
  ["Koppel je Spotify", "Eén keer, in het dashboard. Alle schermen tonen daarna wat je account speelt.", 3],
  ["Start een Jam", "Plak de link in het dashboard. De QR-code staat op elk scherm en je vrienden scannen hem.", 1],
];

export function Steps() {
  const root = useRef(null);
  useGSAP(() => {
    const mm = gsap.matchMedia();
    mm.add("(prefers-reduced-motion: no-preference)", () => {
      gsap.fromTo(".steps-line", { scaleX: 0 }, { scaleX: 1, ease: "none",
        scrollTrigger: { trigger: ".steps", start: "top 75%", end: "bottom 60%", scrub: 1 } });
      gsap.from(".step", { y: 50, opacity: 0, duration: 0.9, ease: "power3.out", stagger: 0.15,
        scrollTrigger: { trigger: ".steps", start: "top 78%" } });
    });
  }, { scope: root });

  return (
    <section ref={root} id="zo-werkt-het">
      <div className="wrap center sec-head">
        <span className="eyebrow">Zo werkt het</span>
        <h2>In tien minuten klaar voor het feest</h2>
      </div>
      <div className="wrap steps">
        <div className="steps-line" aria-hidden="true" />
        {STEPS.map(([title, text, min], i) => (
          <div key={title} className="step">
            <div className="n">{i + 1}</div>
            <h3>{title}</h3>
            <p>{text}</p>
            <span className="time">± <CountUp to={min} from={0} duration={1.4} /> {min === 1 ? "minuut" : "minuten"}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

// Opens the visitor's own Home Assistant (via my.home-assistant.io) and adds SpotiParty to HACS as a dashboard card.
const HACS = "https://my.home-assistant.io/redirect/hacs_repository/?owner=CodeAura&repository=SpotiParty&category=plugin";

const FREE = ["Windows- en Mac-app, werkt zichzelf bij", "Hub met dashboard op je telefoon", "Songteksten, Jam-QR en Hierna",
  "Meldingen, pauze, gasten-wifi en berichten van gasten", "Android TV, Raspberry Pi, Home Assistant, Linux-server en Proxmox",
  "Feestspellen: Raad het nummer, Muziekbingo, stemmen en de winnaar van de avond",
  "Open source, op GitHub"];

export function Pricing() {
  const root = useRef(null);
  const rel = useLatestRelease();
  useGSAP(() => {
    const mm = gsap.matchMedia();
    mm.add("(prefers-reduced-motion: no-preference)", () => {
      gsap.from(".price-wrap", { y: 70, opacity: 0, duration: 1, ease: "power3.out", stagger: 0.12,
        scrollTrigger: { trigger: ".prices", start: "top 80%" } });
    });
  }, { scope: root });

  return (
    <section ref={root} id="prijzen">
      <div className="wrap center sec-head">
        <span className="eyebrow">Prijzen</span>
        <h2>Gratis feest, spellen inbegrepen.</h2>
        <p className="lead">SpotiParty is open source en gratis: de apps, de Hub en de feestspellen.</p>
      </div>
      <div className="wrap prices single">
        <div className="price-wrap">
          <SpotlightCard className="price" spotlightColor="rgba(30, 215, 96, 0.16)" theme="dark">
            <h3>Gratis</h3>
            <p className="for">Alles om van elk scherm een feestscherm te maken</p>
            <div className="amount">€0 <small>voor altijd</small></div>
            <ul>{FREE.map((t) => <li key={t}>{t}</li>)}</ul>
            <div className="downloads">
              <a className="btn btn-primary" href={rel.exe}><Download size={18} strokeWidth={2.25} aria-hidden="true" />Windows</a>
              <a className="btn btn-ghost" href={rel.dmg}><Download size={18} strokeWidth={2.25} aria-hidden="true" />Mac</a>
              <a className="btn btn-ha hacs" href={HACS} target="_blank" rel="noopener noreferrer">
                <House size={18} strokeWidth={2.25} aria-hidden="true" />Home Assistant via HACS</a>
            </div>
            <p className="dl-note">
              {rel.version ? `Versie ${rel.version}. ` : ""}Mac met Intel? <a href={rel.intel}>Deze .dmg</a>. <a href={rel.page}>Alle downloads en de broncode</a>
            </p>
          </SpotlightCard>
        </div>
      </div>
      <p className="note">Spotify Premium is nodig om een Jam te starten.</p>
    </section>
  );
}

const FAQ = [
  ["Heb ik Spotify Premium nodig?", "Om een Jam te starten wel: zo werkt Spotify. Wat er speelt en de songteksten tonen werkt met elk Spotify-account."],
  ["Wat is de Hub?", "Een klein programma op je pc, Mac, Raspberry Pi, Linux-server of Proxmox. Daar koppel je één keer Spotify en je Jam-link, en vanuit het dashboard op je telefoon bestuur je alle schermen."],
  ["Hoe krijgt mijn tv updates?", "Vanzelf. De tv-app toont het scherm rechtstreeks van je Hub. Werkt de Hub zichzelf bij, dan heeft de tv de nieuwe versie zodra je SpotiParty opent."],
  ["Is SpotiParty echt gratis?", "Ja. SpotiParty is open source: de apps, de Hub en de broncode staan gratis op GitHub, met updates. De Windows- en Mac-app werken zichzelf bij."],
  ["Kunnen mijn vrienden de muziek overnemen?", "Nee. Zet in je Jam de optie Gasten mogen afspelen bedienen uit, dan kunnen ze alleen nummers toevoegen. Overslaan kan alleen als jij de Skip-stemmen aanzet, en dan pas bij genoeg stemmen."],
  ["Werkt het op mijn tv?", "Op tv's en mediaspelers met Android TV of Google TV, Android 8 of nieuwer. Samsung (Tizen) en LG (webOS) worden niet ondersteund; sluit daar een pc, Mac of Raspberry Pi aan met HDMI."],
  ["Werkt het ook zonder Spotify, met Sonos bijvoorbeeld?", "Via Home Assistant werkt SpotiParty met elke media player: Sonos, Cast, Music Assistant, Plex en meer."],
  ["Ik heb een Proxmox-server. Kan de Hub daarop?", "Ja. Plak één commando in de shell van je Proxmox-host: dat maakt een kleine Debian-container met de Hub erin, die zichzelf elke nacht bijwerkt. Zie de handleiding, onder Hub op Proxmox."],
  ["Wat doen jullie met mijn gegevens?", "Niets. We hebben geen server die meekijkt. Je Spotify-login en instellingen blijven op je eigen Hub, in je eigen netwerk."],
];

function FaqItem({ q, a }) {
  const [open, setOpen] = useState(false);
  const body = useRef(null);
  const { contextSafe } = useGSAP({ scope: body });
  const toggle = contextSafe(() => {
    const next = !open;
    setOpen(next);
    gsap.to(body.current, { height: next ? "auto" : 0, duration: 0.5, ease: "power3.inOut",
      onComplete: () => ScrollTrigger.refresh() });
  });
  return (
    <div className={`faq-item${open ? " open" : ""}`}>
      <button className="faq-q" aria-expanded={open} onClick={toggle}>{q}<span className="plus" aria-hidden="true"><Plus size={16} strokeWidth={2.5} /></span></button>
      <div ref={body} className="faq-a" role="region"><p>{a}</p></div>
    </div>
  );
}

export function Faq() {
  const root = useRef(null);
  useGSAP(() => {
    const mm = gsap.matchMedia();
    mm.add("(prefers-reduced-motion: no-preference)", () => {
      gsap.from(".faq-item", { y: 30, opacity: 0, duration: 0.7, ease: "power3.out", stagger: 0.06,
        scrollTrigger: { trigger: ".faq", start: "top 82%" } });
    });
  }, { scope: root });
  return (
    <section ref={root} id="faq">
      <div className="wrap center sec-head">
        <span className="eyebrow">Vragen</span>
        <h2>Veelgestelde vragen</h2>
      </div>
      <div className="wrap faq">{FAQ.map(([q, a]) => <FaqItem key={q} q={q} a={a} />)}</div>
    </section>
  );
}

export function Final() {
  const root = useRef(null);
  useGSAP(() => {
    const mm = gsap.matchMedia();
    mm.add("(prefers-reduced-motion: no-preference)", () => {
      gsap.from(".logo", { scale: 0.4, rotate: -20, opacity: 0, duration: 1.1, ease: "back.out(1.8)",
        scrollTrigger: { trigger: root.current, start: "top 70%" } });
      gsap.fromTo(".final-bg", { scale: 0.7, opacity: 0 }, { scale: 1.1, opacity: 1, ease: "none",
        scrollTrigger: { trigger: root.current, start: "top bottom", end: "center center", scrub: 1 } });
    });
  }, { scope: root });
  return (
    <section ref={root} className="final" id="contact">
      <div className="final-bg" aria-hidden="true" />
      <div className="wrap">
        <img className="logo" src="/assets/icon.png" alt="" width="84" height="84" />
        <SplitText text="Klaar voor het volgende feest?" tag="h2" splitType="words" delay={80} duration={1}
          from={{ opacity: 0, y: 50 }} to={{ opacity: 1, y: 0 }} textAlign="center" />
        <p className="lead">Zet SpotiParty vanavond nog op je scherm. Gratis en open source.</p>
        <Magnet padding={60} magnetStrength={3}><a className="btn btn-primary" href="#prijzen">Download gratis</a></Magnet>
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="footer">
      <div className="wrap">
        <span>© 2026 SpotiParty</span>
        <nav aria-label="Voettekst">
          <a href="https://spotiparty.gitbook.io/spotiparty/">Handleiding</a>
          <a href="https://github.com/CodeAura/SpotiParty/releases/latest">Downloads</a>
          <a href="https://github.com/CodeAura/SpotiParty">GitHub</a>
        </nav>
        <p className="legal">SpotiParty heeft niets te maken met Spotify AB en is niet door Spotify goedgekeurd. Spotify en Jam
          zijn handelsmerken van Spotify AB. Songteksten komen van lrclib.net.</p>
      </div>
    </footer>
  );
}
