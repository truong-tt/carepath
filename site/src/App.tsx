import { useEffect, useRef, useState } from "react";
import LandingPage from "./LandingPage";
import ScribeTool from "./scribe/ScribeTool";
import { copyFor } from "./content/strings";
import type { Language } from "./demo/types";

export default function App() {
  const [language, setLanguage] = useState<Language>(() => {
    const saved = localStorage.getItem("carepath-demo-language");
    return saved === "en" ? "en" : "vi";
  });
  // Hash route: "#/scribe" opens the Scribe tool; every other hash is a
  // landing-page anchor (#demo, #scribe overview, #safety, ...).
  const [route, setRoute] = useState(() => window.location.hash);
  const wasScribeTool = useRef(route === "#/scribe");

  useEffect(() => {
    document.documentElement.lang = language;
    document.title = copyFor(language).metadata.title;
    document
      .querySelector('meta[name="description"]')
      ?.setAttribute("content", copyFor(language).metadata.description);
    localStorage.setItem("carepath-demo-language", language);
  }, [language]);

  useEffect(() => {
    const onHashChange = () => setRoute(window.location.hash);
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const isScribeTool = route === "#/scribe";

  useEffect(() => {
    if (isScribeTool) window.scrollTo(0, 0);
  }, [isScribeTool]);

  useEffect(() => {
    let frame: number | undefined;
    if (wasScribeTool.current && !isScribeTool) {
      frame = window.requestAnimationFrame(() => {
        const anchor = document.getElementById(route.slice(1) || "top") ??
          document.getElementById("top");
        anchor?.scrollIntoView();
        anchor?.focus({ preventScroll: true });
      });
    }
    wasScribeTool.current = isScribeTool;
    return () => {
      if (frame !== undefined) window.cancelAnimationFrame(frame);
    };
  }, [isScribeTool, route]);

  return isScribeTool ? (
    <ScribeTool language={language} onLanguageChange={setLanguage} />
  ) : (
    <LandingPage language={language} onLanguageChange={setLanguage} />
  );
}
