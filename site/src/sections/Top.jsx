// The concept banner, the navigation bar and the hero with the TV that straightens out while you scroll.
import { useRef } from "react";
import { gsap, ScrollTrigger, useGSAP } from "../lib/motion.js";
import Aurora from "../components/reactbits/Aurora/Aurora.jsx";
import SplitText from "../components/reactbits/SplitText/SplitText.jsx";
import BlurText from "../components/reactbits/BlurText/BlurText.jsx";
import Magnet from "../components/reactbits/Magnet/Magnet.jsx";
import Pic from "../components/Pic.jsx";

export function Nav() {
  const ref = useRef(null);
  useGSAP(() => {
    ScrollTrigger.create({
      start: 40,
      end: "max",
      onToggle: (self) => ref.current.classList.toggle("solid", self.isActive),
    });
  }, { scope: ref });
  return (
    <>
      <div className="concept"><span className="tag">Nieuw</span>SpotiParty is nu open source en gratis. Het Feestpakket met feestspellen komt binnenkort.</div>
      <nav ref={ref} className="nav">
        <div className="wrap">
          <a className="brand" href="#top"><img src="/assets/icon.png" alt="" width="34" height="34" />SpotiParty</a>
          <div className="nav-links">
            <a href="#functies">Functies</a>
            <a href="#hub">Hub</a>
            <a href="#feest">Feestspellen</a>
            <a href="#overal">Waar het werkt</a>
            <a href="#prijzen">Prijzen</a>
            <a href="#faq">Vragen</a>
          </div>
          <Magnet padding={40} magnetStrength={4} wrapperClassName="btn-wrap">
            <a className="btn btn-primary" href="#prijzen">Download</a>
          </Magnet>
        </div>
      </nav>
    </>
  );
}

export function Hero() {
  const root = useRef(null);
  useGSAP(() => {
    const mm = gsap.matchMedia();
    mm.add("(prefers-reduced-motion: no-preference)", () => {
      gsap.from(".grad-word", { yPercent: 70, opacity: 0, filter: "blur(14px)", duration: 1.3, ease: "expo.out", delay: 0.75 });
      gsap.from(".hero-ctas > *, .trust span", { y: 26, opacity: 0, duration: 0.9, ease: "power3.out", stagger: 0.07, delay: 1.25 });
      // The TV lies back a little and straightens out as it scrolls into view.
      gsap.fromTo(".tv", { rotateX: 28, scale: 0.84, y: 30 }, {
        rotateX: 0, scale: 1, y: 0, ease: "none",
        scrollTrigger: { trigger: ".tv-stage", start: "top 92%", end: "top 12%", scrub: 1 },
      });
      gsap.fromTo(".tv-glow", { opacity: 0.2, scale: 0.7 }, {
        opacity: 1, scale: 1, ease: "none",
        scrollTrigger: { trigger: ".tv-stage", start: "top 92%", end: "top 12%", scrub: 1 },
      });
      // The aurora drifts away a bit slower than the page.
      gsap.to(".hero-bg", { yPercent: 22, ease: "none", scrollTrigger: { trigger: root.current, start: "top top", end: "bottom top", scrub: true } });
    });
  }, { scope: root });

  return (
    <header ref={root} id="top" className="hero">
      <div className="hero-bg" aria-hidden="true">
        <Aurora colorStops={["#241245", "#b8346b", "#241245"]} amplitude={0.7} blend={0.4} speed={0.4} height={0.4} />
      </div>
      <div className="wrap">
        <span className="eyebrow">Voor feestjes, borrels en zondagmiddagen</span>
        <h1>
          <SplitText text="Maak van elk scherm een" tag="span" splitType="chars" delay={28} duration={1.1}
            from={{ opacity: 0, y: 70 }} to={{ opacity: 1, y: 0 }} threshold={0} rootMargin="0px" textAlign="center" />{" "}
          <span className="grad-word grad-text">feestscherm.</span>
        </h1>
        <BlurText className="lead" animateBy="words" delay={35} stepDuration={0.3} direction="bottom" threshold={0}
          text="Het nummer dat speelt groot op je tv, pc, Mac of Home Assistant-dashboard. De songtekst loopt in de maat mee, je vrienden zetten met één QR-code hun nummers in de wachtrij, kiezen het volgende nummer en spelen muziekbingo, en vanuit één dashboard bestuur je alle schermen in huis." />
        <div className="hero-ctas">
          <Magnet padding={50} magnetStrength={3}><a className="btn btn-primary" href="#prijzen">Download gratis</a></Magnet>
          <Magnet padding={50} magnetStrength={3}><a className="btn btn-ghost" href="#zo-werkt-het">Zo werkt het</a></Magnet>
        </div>
        <div className="trust"><span>Gratis en open source</span><span>Werkt met je eigen Spotify</span><span>Windows, Mac, tv en Home Assistant</span></div>
      </div>
      <div className="tv-stage">
        <div className="tv">
          <div className="tv-glow" aria-hidden="true" />
          <div className="tv-frame">
            <Pic name="screen" eager width="1600" height="900"
              alt="SpotiParty op een tv: de hoes van het nummer, de meelopende songtekst, de komende nummers en een QR-code voor de Spotify Jam" />
          </div>
          <div className="tv-stand" />
        </div>
      </div>
    </header>
  );
}
