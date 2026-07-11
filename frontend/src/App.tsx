import { useEffect, useState } from "react";

import "./App.css";
import logoUrl from "./assets/carepath.svg";
import { createSession } from "./api";
import { AdminReview } from "./components/AdminReview";
import { ConsentGate, type ConsentPayload } from "./components/ConsentGate";
import { InterpreterConsole } from "./components/InterpreterConsole";
import { IntentQuiz, type Intent } from "./components/IntentQuiz";
import { copy, initialLanguage, persistLanguage, type Language } from "./copy";

function ProductShell({ language, setLanguage }: { language: Language; setLanguage: (language: Language) => void }) {
  const text = copy[language];
  const publicSiteUrl = import.meta.env.VITE_PUBLIC_SITE_URL;
  const allProductsHref = (() => {
    if (!publicSiteUrl) return "/";
    const url = new URL(publicSiteUrl);
    url.searchParams.set("lang", language);
    return url.href;
  })();

  return (
    <header className="product-shell" lang={language}>
      <nav className="product-breadcrumb" aria-label={text.breadcrumb}>
        <ol>
          <li>
            <a className="product-brand" href="/" aria-label="CarePath">
              <img src={logoUrl} alt="" />
              <span>CarePath</span>
            </a>
          </li>
          <li aria-hidden="true">/</li>
          <li aria-current="page">
            {text.productName}
          </li>
        </ol>
      </nav>
      <p className="product-status">
        <span aria-hidden="true" />
        {text.status}
      </p>
      <div className="product-shell__actions">
        <a className="all-products" href={allProductsHref}>
          {text.allProducts}
        </a>
        <div className="language-toggle" role="group" aria-label={text.language}>
          <button
            aria-pressed={language === "vi"}
            type="button"
            onClick={() => setLanguage("vi")}
          >
            VI
          </button>
          <button
            aria-pressed={language === "en"}
            type="button"
            onClick={() => setLanguage("en")}
          >
            EN
          </button>
        </div>
      </div>
    </header>
  );
}

function App() {
  const [language, setLanguage] = useState<Language>(initialLanguage);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [intent, setIntent] = useState<Intent | null>(null);

  useEffect(() => {
    persistLanguage(language);
    document.documentElement.lang = language;
    document.title = copy[language].title;
  }, [language]);

  async function handleConsent(consent: ConsentPayload) {
    setStarting(true);
    setError(null);
    try {
      const result = await createSession({ consent });
      setSessionId(result.session_id);
    } catch {
      setError(copy[language].consent.startError);
    } finally {
      setStarting(false);
    }
  }

  let content;
  if (window.location.pathname === "/admin") {
    content = <AdminReview language={language} />;
  } else if (sessionId) {
    content = <InterpreterConsole initialSpeaker={intent?.direction === "en-vi" ? "patient" : "doctor"} language={language} sessionId={sessionId} />;
  } else if (!intent) {
    content = <IntentQuiz language={language} onComplete={setIntent} />;
  } else {
    content = <ConsentGate error={error} isSubmitting={starting} language={language} onConsent={handleConsent} />;
  }

  return (
    <div className="product-app" lang={language}>
      <ProductShell language={language} setLanguage={setLanguage} />
      {content}
    </div>
  );
}

export default App;
