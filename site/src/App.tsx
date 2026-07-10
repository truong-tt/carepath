import { useEffect, useState } from "react";
import LandingPage from "./LandingPage";
import ScribeTool from "./scribe/ScribeTool";
import type { Language } from "./demo/types";

export default function App() {
  const [language, setLanguage] = useState<Language>(() => {
    const saved = localStorage.getItem("carepath-demo-language");
    return saved === "en" ? "en" : "vi";
  });
  // Hash route: "#/scribe" opens the Scribe tool; every other hash is a
  // landing-page anchor (#demo, #scribe overview, #safety, ...).
  const [route, setRoute] = useState(() => window.location.hash);

  useEffect(() => {
    document.documentElement.lang = language;
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

  return isScribeTool ? (
    <ScribeTool language={language} onLanguageChange={setLanguage} />
  ) : (
    <LandingPage language={language} onLanguageChange={setLanguage} />
  );
}
