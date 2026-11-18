// Lenis smooth scrolling, driven by GSAP's ticker so ScrollTrigger and Lenis stay in step.
// Anchor links (#prijzen) scroll smoothly too. Off for visitors who prefer reduced motion.
import { useEffect } from "react";
import Lenis from "lenis";
import "lenis/dist/lenis.css";
import { gsap, ScrollTrigger, reducedMotion } from "./motion.js";

let lenis = null;

export function scrollToTarget(target) {
  const el = typeof target === "string" ? document.querySelector(target) : target;
  if (!el) return;
  if (lenis) lenis.scrollTo(el, { offset: -72, duration: 1.4 });
  else el.scrollIntoView({ behavior: reducedMotion() ? "auto" : "smooth" });
}

export function useSmoothScroll() {
  useEffect(() => {
    const onClick = (e) => {
      const a = e.target.closest('a[href^="#"]');
      if (!a) return;
      const id = a.getAttribute("href");
      if (id.length < 2 || !document.querySelector(id)) return;
      e.preventDefault();
      scrollToTarget(id);
      history.replaceState(null, "", id);
    };
    document.addEventListener("click", onClick);
    // Fonts and images change the layout: recalculate the triggers once they are in.
    const refresh = () => ScrollTrigger.refresh();
    document.fonts?.ready.then(refresh);
    window.addEventListener("load", refresh, { once: true });

    let tick = null;
    if (!reducedMotion()) {
      lenis = new Lenis({ lerp: 0.09, smoothWheel: true, wheelMultiplier: 0.95 });
      lenis.on("scroll", ScrollTrigger.update);
      tick = (time) => lenis.raf(time * 1000);
      gsap.ticker.add(tick);
      gsap.ticker.lagSmoothing(0);
    }
    return () => {
      document.removeEventListener("click", onClick);
      window.removeEventListener("load", refresh);
      if (tick) gsap.ticker.remove(tick);
      lenis?.destroy();
      lenis = null;
    };
  }, []);
}
