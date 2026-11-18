# SpotiParty website

The site at [spotiparty.netlify.app](https://spotiparty.netlify.app): a Vite + React app with
[GSAP](https://gsap.com) (ScrollTrigger, via `@gsap/react`), [Lenis](https://lenis.darkroom.engineering) smooth scrolling
and components from [React Bits](https://reactbits.dev).

```bash
cd site
npm install
npm run dev       # http://localhost:5173
npm run build     # site/dist, what Netlify publishes
```

Netlify builds it with the settings in `../netlify.toml` (base `site`, command `npm ci && npm run build`, publish `dist`).

## Layout

| Path | What |
|---|---|
| `src/App.jsx` | The page: sections in order, and Lenis |
| `src/lib/motion.js` | GSAP plugins (ScrollTrigger, useGSAP) and the reduced-motion check |
| `src/lib/useSmoothScroll.js` | Lenis on GSAP's ticker, kept in sync with ScrollTrigger; smooth `#anchor` links |
| `src/sections/Top.jsx` | Concept banner, navigation, hero (Aurora, SplitText, BlurText) and the TV that straightens out |
| `src/sections/Middle.jsx` | "Wat je ziet" (pinned, four hotspots), features (SpotlightCard), the Hub (ScrollReveal) |
| `src/sections/Bottom.jsx` | Party games (pinned horizontal panels), platforms (TiltedCard), steps (CountUp), prices, FAQ, final call, footer |
| `src/components/reactbits/` | React Bits components, unchanged from `https://reactbits.dev/r/<Name>-JS-CSS.json` |
| `public/assets/` | Images (WebP with a JPG fallback): screenshots of the real screen, dashboard and guest page |

## Motion

Every animation is set up in `useGSAP()` with a `scope`, inside `gsap.matchMedia()`: with *reduce motion* on, there
is no Lenis, no pinning and no scroll animation, and the content is simply there. ScrollTriggers are created top to
bottom in page order (the pinned "Wat je ziet" and party sections add scroll length).

The screenshots in `public/assets/` come from the real SpotiParty screen and Hub dashboard with a fictional song and an
example network address (see the README images in `../docs/images/`).
