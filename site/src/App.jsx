import { useSmoothScroll } from "./lib/useSmoothScroll.js";
import { Nav, Hero } from "./sections/Top.jsx";
import { Explain, Features, Hub } from "./sections/Middle.jsx";
import { Party, Platforms, Steps, Pricing, Faq, Final, Footer } from "./sections/Bottom.jsx";

export default function App() {
  useSmoothScroll();
  return (
    <>
      <Nav />
      <main>
        <Hero />
        <Explain />
        <Features />
        <Hub />
        <Party />
        <Platforms />
        <Steps />
        <Pricing />
        <Faq />
        <Final />
      </main>
      <Footer />
    </>
  );
}
