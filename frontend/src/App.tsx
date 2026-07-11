import { useEffect, useState } from "react";

import "./App.css";
import logoUrl from "./assets/carepath.svg";
import { createSession } from "./api";
import { AdminReview } from "./components/AdminReview";
import { ConsentGate, type ConsentPayload } from "./components/ConsentGate";
import { InterpreterConsole } from "./components/InterpreterConsole";
import { copy, initialLanguage, persistLanguage, type Language } from "./copy";

function ProductShell({ language, setLanguage }: { language: Language; setLanguage: (language: Language) => void }) {
  const text = copy[language];

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
        <a className="all-products" href="/">
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
      setError("Không thể bắt đầu phiên dịch. Vui lòng kiểm tra kết nối máy chủ.");
    } finally {
      setStarting(false);
    }
  }

  let content;
  if (window.location.pathname === "/admin") {
    content = <AdminReview language={language} />;
  } else if (sessionId) {
    content = <InterpreterConsole language={language} sessionId={sessionId} />;
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
