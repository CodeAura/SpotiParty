// "Wat je ziet" (the screen, explained while pinned), the features and the Hub.
import { useRef } from "react";
import { gsap, ScrollTrigger, useGSAP } from "../lib/motion.js";
import SpotlightCard from "../components/reactbits/SpotlightCard/SpotlightCard.jsx";
import ScrollReveal from "../components/reactbits/ScrollReveal/ScrollReveal.jsx";
import ShinyText from "../components/reactbits/ShinyText/ShinyText.jsx";
import Pic from "../components/Pic.jsx";

const SPOTS = [
  { box: [3.9, 13.1, 26.5, 57.6], title: "Wat er speelt",
    text: "De hoes, titel en artiest, groot in beeld. De hoes kleurt de hele achtergrond en de balk loopt mee met het nummer." },
  { box: [32.5, 27.8, 38.1, 28.3], title: "De songtekst, in de maat",
    text: "De regel die nu gezongen wordt staat groot in het midden. Teksten komen van lrclib.net: gratis, zonder account." },
  { box: [3.9, 71.3, 26.5, 11.8], title: "Hierna",
    text: "De komende 1, 3 of 5 nummers uit de wachtrij. Zo weet iedereen wanneer zijn nummer aan de beurt is." },
  { box: [63.1, 76.7, 34.1, 20.7], title: "Eén QR-code voor iedereen",
    text: "Vrienden scannen en zetten hun eigen nummers in de Jam. Met de feestspellen aan leidt de code naar de gastenpagina." },
];

export function Explain() {
  const root = useRef(null);
  useGSAP(() => {
    const mm = gsap.matchMedia();
    mm.add("(prefers-reduced-motion: no-preference)", () => {
      const spots = gsap.utils.toArray(".hotspot");
      const items = gsap.utils.toArray(".explain-item");
      const dots = gsap.utils.toArray(".explain-dots i");
      const tl = gsap.timeline({
        defaults: { ease: "power2.out", duration: 0.5 },
        scrollTrigger: {
          trigger: ".explain-pin", start: "top top", end: () => "+=" + window.innerHeight * 3, pin: true, scrub: 0.8,
          // The dots follow the scroll position directly (not the eased timeline), so they never disagree.
          onUpdate: (self) => {
            const on = Math.min(spots.length - 1, Math.floor(self.progress * spots.length));
            dots.forEach((d, i) => d.classList.toggle("on", i === on));
          },
        },
      });
      spots.forEach((spot, i) => {
        if (i > 0) {
          tl.to(spots[i - 1], { opacity: 0 }, `s${i}`)
            .to(items[i - 1], { opacity: 0, y: -24 }, `s${i}`);
        }
        tl.fromTo(spot, { opacity: 0, scale: 1.08 }, { opacity: 1, scale: 1 }, i ? `s${i}+=0.2` : 0)
          .fromTo(items[i], { opacity: 0, y: 30 }, { opacity: 1, y: 0 }, i ? `s${i}+=0.25` : 0.05)
          .to({}, { duration: 0.6 });
      });
    });
    mm.add("(prefers-reduced-motion: reduce)", () => {
      gsap.set(".explain-item", { position: "static", opacity: 1, marginBottom: 24 });
    });
  }, { scope: root });

  return (
    <section ref={root} className="explain" aria-labelledby="explain-title">
      <div className="explain-pin">
        <div className="wrap explain-grid">
          <div className="shot">
            <Pic name="screen" width="1600" height="900" alt="" />
            {SPOTS.map((s, i) => (
              <div key={i} className="hotspot" style={{ left: `${s.box[0]}%`, top: `${s.box[1]}%`, width: `${s.box[2]}%`, height: `${s.box[3]}%` }}>
                <b>{i + 1}</b>
              </div>
            ))}
          </div>
          <div>
            <span className="eyebrow grad-text" id="explain-title">Wat je ziet</span>
            <div className="explain-items">
              {SPOTS.map((s, i) => (
                <div key={i} className="explain-item">
                  <span className="num">0{i + 1}</span>
                  <h3>{s.title}</h3>
                  <p>{s.text}</p>
                </div>
              ))}
            </div>
            <div className="explain-dots" aria-hidden="true">{SPOTS.map((_, i) => <i key={i} />)}</div>
          </div>
        </div>
      </div>
    </section>
  );
}

const FEATURES = [
  ["🎤", "Meezingen", "De songtekst loopt regel voor regel mee. De regel die nu gezongen wordt staat groot in beeld."],
  ["📱", "Jam-QR voor iedereen", "Vrienden scannen de code en zetten hun nummers in de wachtrij. Overslaan of het volume veranderen kunnen ze niet."],
  ["🌅", "Sfeer uit de hoes", "De hoes kleurt het hele scherm, en de kleuren lopen mee met elk nieuw nummer."],
  ["⏭️", "Hierna in de wachtrij", "Iedereen ziet welke nummers eraan komen: één, drie of vijf, zoals jij wilt."],
  ["🎉", "Feestspellen", "Gasten stemmen om een nummer over te slaan, of spelen Raad het nummer op hun telefoon."],
  ["🔒", "Privé", "Geen account bij ons en geen tracking. Alles draait in je eigen netwerk, op je eigen Hub."],
];

export function Features() {
  const root = useRef(null);
  useGSAP(() => {
    const mm = gsap.matchMedia();
    mm.add("(prefers-reduced-motion: no-preference)", () => {
      gsap.set(".feature-wrap", { opacity: 0, y: 50 });
      ScrollTrigger.batch(".feature-wrap", {
        start: "top 88%",
        onEnter: (els) => gsap.to(els, { opacity: 1, y: 0, duration: 0.9, ease: "power3.out", stagger: 0.09, overwrite: true }),
      });
      gsap.from(".features-head > *", { y: 30, opacity: 0, stagger: 0.1, duration: 0.9, ease: "power3.out",
        scrollTrigger: { trigger: ".features-head", start: "top 85%" } });
    });
  }, { scope: root });

  return (
    <section ref={root} id="functies">
      <div className="wrap center sec-head features-head">
        <span className="eyebrow grad-text">Functies</span>
        <h2>Alles wat een feest nodig heeft</h2>
        <p className="lead">Geen telefoon die rondgaat. Iedereen ziet wat er speelt, zingt mee en kiest zelf het volgende nummer.</p>
      </div>
      <div className="wrap features">
        {FEATURES.map(([icon, title, text]) => (
          <div key={title} className="feature-wrap">
            <SpotlightCard className="feature" spotlightColor="rgba(255, 78, 138, 0.22)" theme="dark">
              <div className="icon" aria-hidden="true">{icon}</div>
              <h3>{title}</h3>
              <p>{text}</p>
            </SpotlightCard>
          </div>
        ))}
      </div>
    </section>
  );
}

const HUB = [
  ["🎵", "Muziek bedienen", "Vorige, pauze, volgende en het volume, op welk apparaat je Spotify ook speelt."],
  ["💬", "Meldingen", "“De pizza's zijn er! 🍕” groot op de schermen die je kiest."],
  ["⏸️", "Korte pauze", "Een aftelklok op alle schermen. De muziek pauzeert en gaat daarna vanzelf verder."],
  ["📶", "Gasten-wifi", "Een QR-code naast de Jam-code: één scan en je gasten zitten op je gastennetwerk."],
  ["🎶", "Eén Jam-link", "Eén keer plakken, en elk scherm in huis toont dezelfde QR-code."],
];

export function Hub() {
  const root = useRef(null);
  useGSAP(() => {
    const mm = gsap.matchMedia();
    mm.add("(prefers-reduced-motion: no-preference)", () => {
      // The dashboard scrolls inside its browser window while the page scrolls past it.
      const view = root.current.querySelector(".browser-view");
      const pic = view.querySelector("picture");
      gsap.fromTo(pic, { y: 0 }, {
        y: () => Math.min(0, view.clientHeight - pic.offsetHeight), ease: "none",
        scrollTrigger: { trigger: ".browser", start: "top 80%", end: "bottom 20%", scrub: 1, invalidateOnRefresh: true },
      });
      gsap.from(".browser", { y: 80, rotate: -2, opacity: 0, duration: 1.2, ease: "power3.out",
        scrollTrigger: { trigger: ".hub-grid", start: "top 80%" } });
      gsap.from(".hub-item", { x: 60, opacity: 0, duration: 0.8, ease: "power3.out", stagger: 0.1,
        scrollTrigger: { trigger: ".hub-list", start: "top 80%" } });
    });
  }, { scope: root });

  return (
    <section ref={root} id="hub" className="hub">
      <div className="wrap">
        <div className="center"><span className="eyebrow"><ShinyText text="De SpotiParty Hub" color="#b3abd1" shineColor="#ffffff" speed={3} /></span></div>
        <ScrollReveal baseOpacity={0.12} enableBlur blurStrength={6} baseRotation={2}>
          Eén dashboard op je telefoon voor alle schermen in huis: de muziek, de Jam, meldingen, een pauze en de gasten-wifi.
        </ScrollReveal>
        <div className="hub-grid">
          <div className="browser">
            <div className="browser-bar"><i /><i /><i /><span>192.168.1.20:8770</span></div>
            <div className="browser-view">
              <Pic name="dashboard" width="1600" height="1519"
                alt="Het SpotiParty Hub-dashboard met de schermen, Muziek bedienen, de Spotify Jam en het Feest-blok" />
            </div>
          </div>
          <div className="hub-list">
            {HUB.map(([icon, title, text]) => (
              <div key={title} className="hub-item">
                <span className="icon" aria-hidden="true">{icon}</span>
                <div><b>{title}</b><span>{text}</span></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
