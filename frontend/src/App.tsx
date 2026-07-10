import { useEffect, useState } from "react";

import "./App.css";
import logoUrl from "./assets/carepath.svg";
import { createSession } from "./api";
import { AdminReview } from "./components/AdminReview";
import { ConsentGate, type ConsentPayload } from "./components/ConsentGate";
import { InterpreterConsole } from "./components/InterpreterConsole";

type Language = "vi" | "en";

const shellCopy = {
  vi: {
    breadcrumb: "Đường dẫn sản phẩm",
    status: "Bản mô phỏng tương tác",
    allProducts: "Tất cả sản phẩm",
    language: "Ngôn ngữ thanh sản phẩm",
  },
  en: {
    breadcrumb: "Product breadcrumb",
    status: "Interactive mock simulation",
    allProducts: "All products",
    language: "Product bar language",
  },
} as const;

function ProductShell() {
  const [language, setLanguage] = useState<Language>(() =>
    localStorage.getItem("carepath-demo-language") === "en" ? "en" : "vi",
  );
  const copy = shellCopy[language];

  useEffect(() => {
    localStorage.setItem("carepath-demo-language", language);
  }, [language]);

  return (
    <header className="product-shell" lang={language}>
      <nav className="product-breadcrumb" aria-label={copy.breadcrumb}>
        <ol>
          <li>
            <a className="product-brand" href="/" aria-label="CarePath">
              <img src={logoUrl} alt="" />
              <span>CarePath</span>
            </a>
          </li>
          <li aria-hidden="true">/</li>
          <li aria-current="page">Interpreter</li>
        </ol>
      </nav>
      <p className="product-status">
        <span aria-hidden="true" />
        {copy.status}
      </p>
      <div className="product-shell__actions">
        <a className="all-products" href="/">
          {copy.allProducts}
        </a>
        <div className="language-toggle" role="group" aria-label={copy.language}>
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
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  async function handleConsent(consent: ConsentPayload) {
    setStarting(true);
    setError(null);
    try {
      const result = await createSession({ consent });
      setSessionId(result.session_id);
    } catch {
      setError("Could not start the session. Check that the backend is running.");
    } finally {
      setStarting(false);
    }
  }

  let content;
  if (window.location.pathname === "/admin") {
    content = <AdminReview />;
  } else if (sessionId) {
    content = <InterpreterConsole sessionId={sessionId} />;
  } else {
    content = <ConsentGate error={error} isSubmitting={starting} onConsent={handleConsent} />;
  }

  return (
    <div className="product-app">
      <ProductShell />
      {content}
    </div>
  );
}

export default App;
