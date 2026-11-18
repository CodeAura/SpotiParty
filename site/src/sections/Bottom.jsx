// Party games (horizontal panels), where it works, the steps, prices, questions, the final call and the footer.
import { useRef, useState } from "react";
import { gsap, ScrollTrigger, useGSAP } from "../lib/motion.js";
import SpotlightCard from "../components/reactbits/SpotlightCard/SpotlightCard.jsx";
import TiltedCard from "../components/reactbits/TiltedCard/TiltedCard.jsx";
import CountUp from "../components/reactbits/CountUp/CountUp.jsx";
import ShinyText from "../components/reactbits/ShinyText/ShinyText.jsx";
import SplitText from "../components/reactbits/SplitText/SplitText.jsx";
import Magnet from "../components/reactbits/Magnet/Magnet.jsx";
import Pic from "../components/Pic.jsx";
import { Tv, Laptop, Apple, Cpu, Server, House } from "lucide-react";

const PANELS = [
  { img: "screen", tag: "Komende nummers", title: "Iedereen weet wat er komt",
    text: "De schermen tonen de volgende één, drie of vijf nummers uit de wachtrij. Kies het aantal in het dashboard." },
  { img: "quiz", tag: "🎤 Raad het nummer", title: "Wie raadt hem het snelst?", phone: true,
    text: "Bij elk nieuw nummer blijven titel en hoes 15 seconden geheim. Gasten raden op hun telefoon: hoe sneller, hoe meer punten." },
  { img: "reveal", tag: "👎 Skip en de top 5", title: "En de winnaar is…",
    text: "Daarna het antwoord en de top 5. Met genoeg Skip-stemmen slaat de Hub het nummer over: het feest beslist mee." },
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
          <span className="eyebrow grad-text">Feestspellen</span>
          <h2>Meer dan meezingen</h2>
        </div>
        <div className="party-track">
          {PANELS.map((p) => (
            <article key={p.img} className="panel">
              <div className="panel-media">
                <Pic name={p.img} width="1600" height="900" alt={p.title} />
                {p.phone && <Pic name="guest" eager className="phone" width="780" height="2200" alt="De gastenpagina op een telefoon: Jam, Skip en het raadvak" />}
              </div>
              <div className="panel-text">
                <span className="panel-tag">{p.tag}</span>
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
  [Apple, "macOS", <>Voor Macs met Apple silicon, werkt zichzelf bij. <a href="https://github.com/CodeAura/SpotiParty/releases/latest">Download de .dmg</a>; Intel volgt.</>],
  [Cpu, "Raspberry Pi", "Een vast feestscherm aan je tv of beamer, en als je wilt ook de Hub."],
  [Server, "Linux-server", "De Hub zonder scherm, op je NAS of thuisserver: met systemd of Docker."],
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
          <span className="eyebrow grad-text">Waar het werkt</span>
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
  ["Installeer de Hub", "De Windows- of Mac-app, een Raspberry Pi of een Linux-server. Je krijgt het adres en de PIN van het dashboard.", 5],
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
        <span className="eyebrow grad-text">Zo werkt het</span>
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

const PRICES = [
  { plan: "Desktop", price: "€9,99", for: "Voor je pc, Mac of beamer",
    items: [["Windows- en Mac-app"], ["Hub met dashboard"], ["Songteksten, Jam-QR en Hierna"], ["Android TV", true], ["Home Assistant", true]] },
  { plan: "Thuis", price: "€14,99", for: "Alle schermen in huis", hot: true,
    items: [["Alles uit Desktop"], ["Android TV-app"], ["Home Assistant-kaart"], ["Raspberry Pi"], ["Feestspellen"]] },
  { plan: "Vrienden", price: "€29,99", for: "Drie keer Thuis, om weg te geven",
    items: [["3 × alles uit Thuis"], ["Per persoon een eigen code"], ["Leuk als cadeau"], ["Zelf te verdelen"], ["Bespaar €15"]] },
];

export function Pricing() {
  const root = useRef(null);
  const dialog = useRef(null);
  const [choice, setChoice] = useState(PRICES[1]);
  useGSAP(() => {
    const mm = gsap.matchMedia();
    mm.add("(prefers-reduced-motion: no-preference)", () => {
      gsap.from(".price-wrap", { y: 70, opacity: 0, duration: 1, ease: "power3.out", stagger: 0.12,
        scrollTrigger: { trigger: ".prices", start: "top 80%" } });
    });
  }, { scope: root });

  const buy = (p) => { setChoice(p); dialog.current?.showModal(); };

  return (
    <section ref={root} id="prijzen">
      <div className="wrap center sec-head">
        <span className="eyebrow grad-text">Prijzen</span>
        <h2>Eén keer betalen, voor altijd feest</h2>
        <p className="lead">Geen abonnement. Updates zitten erbij.</p>
      </div>
      <div className="wrap prices">
        {PRICES.map((p) => (
          <div key={p.plan} className="price-wrap">
            <SpotlightCard className={`price${p.hot ? " hot" : ""}`} spotlightColor="rgba(123, 60, 255, 0.25)" theme="dark">
              {p.hot && <span className="badge"><ShinyText text="Meest gekozen" color="#ff9fbf" shineColor="#ffffff" speed={2.5} /></span>}
              <h3>{p.plan}</h3>
              <p className="for">{p.for}</p>
              <div className="amount">{p.price} <small>eenmalig</small></div>
              <ul>{p.items.map(([t, no]) => <li key={t} className={no ? "no" : ""}>{t}</li>)}</ul>
              <button className={`btn ${p.hot ? "btn-primary" : "btn-ghost"}`} onClick={() => buy(p)}>Koop {p.plan}</button>
            </SpotlightCard>
          </div>
        ))}
      </div>
      <p className="note">Concept-prijzen, inclusief btw. Spotify Premium is nodig om een Jam te starten.</p>

      <dialog ref={dialog} className="checkout" aria-labelledby="co-title" onClick={(e) => e.target === dialog.current && dialog.current.close()}>
        <h3 id="co-title">Bijna klaar</h3>
        <p>De winkel gaat binnenkort open. In dit concept wordt er nog niets afgerekend.</p>
        <div className="summary"><span>SpotiParty {choice.plan}</span><span>{choice.price}</span></div>
        <button className="btn btn-primary" onClick={() => dialog.current.close()}>Oké</button>
      </dialog>
    </section>
  );
}

const FAQ = [
  ["Heb ik Spotify Premium nodig?", "Om een Jam te starten wel: zo werkt Spotify. Wat er speelt en de songteksten tonen werkt met elk Spotify-account."],
  ["Wat is de Hub?", "Een klein programma op je pc, Mac, Raspberry Pi of Linux-server. Daar koppel je één keer Spotify en je Jam-link, en vanuit het dashboard op je telefoon bestuur je alle schermen."],
  ["Hoe krijgt mijn tv updates?", "Vanzelf. De tv-app toont het scherm rechtstreeks van je Hub. Werkt de Hub zichzelf bij, dan heeft de tv de nieuwe versie zodra je SpotiParty opent."],
  ["Is het een abonnement?", "Nee. Je betaalt één keer en houdt SpotiParty, met updates. De Windows- en Mac-app werken zichzelf bij."],
  ["Kunnen mijn vrienden de muziek overnemen?", "Nee. Zet in je Jam de optie Gasten mogen afspelen bedienen uit, dan kunnen ze alleen nummers toevoegen. Overslaan kan alleen als jij de Skip-stemmen aanzet, en dan pas bij genoeg stemmen."],
  ["Werkt het op mijn tv?", "Op tv's en mediaspelers met Android TV of Google TV, Android 8 of nieuwer. Samsung (Tizen) en LG (webOS) worden niet ondersteund; sluit daar een pc, Mac of Raspberry Pi aan met HDMI."],
  ["Werkt het ook zonder Spotify, met Sonos bijvoorbeeld?", "Via Home Assistant werkt SpotiParty met elke media player: Sonos, Cast, Music Assistant, Plex en meer."],
  ["Wat doen jullie met mijn gegevens?", "Niets. We hebben geen server die meekijkt. Je Spotify-login en instellingen blijven op je eigen Hub, in je eigen netwerk."],
  ["Kan ik mijn geld terugkrijgen?", "Ja, binnen 14 dagen, zonder vragen."],
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
      <button className="faq-q" aria-expanded={open} onClick={toggle}>{q}<span className="plus" aria-hidden="true">+</span></button>
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
        <span className="eyebrow grad-text">Vragen</span>
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
        <p className="lead">Zet SpotiParty vanavond nog op je scherm.</p>
        <Magnet padding={60} magnetStrength={3}><a className="btn btn-primary" href="#prijzen">Bekijk de prijzen</a></Magnet>
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
