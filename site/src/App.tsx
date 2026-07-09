import { useEffect, useState } from "react";
import LandingPage from "./LandingPage";
import type { Language } from "./demo/types";

export default function App() {
  const [language, setLanguage] = useState<Language>(() => {
    const saved = localStorage.getItem("carepath-demo-language");
    return saved === "en" ? "en" : "vi";
  });

  useEffect(() => {
    document.documentElement.lang = language;
    localStorage.setItem("carepath-demo-language", language);
  }, [language]);

  return (
    <LandingPage language={language} onLanguageChange={setLanguage} />
  );
}
