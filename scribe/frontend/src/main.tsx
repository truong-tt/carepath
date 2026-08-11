import React from "react";
import ReactDOM from "react-dom/client";
// Geist carries the product surfaces. Be Vietnam Pro is drawn for Vietnamese by
// a Vietnamese foundry and carries the public page — the argument there is about
// Vietnamese medical language, so the letterforms should be too. Vietnamese
// subset first per weight so it wins the match; latin backfills.
import "@fontsource/geist/latin-400.css";
import "@fontsource/geist/vietnamese-400.css";
import "@fontsource/geist/latin-500.css";
import "@fontsource/geist/vietnamese-500.css";
import "@fontsource/geist/latin-600.css";
import "@fontsource/geist/vietnamese-600.css";
import "@fontsource/geist/latin-700.css";
import "@fontsource/geist/vietnamese-700.css";
import "@fontsource/be-vietnam-pro/latin-400.css";
import "@fontsource/be-vietnam-pro/vietnamese-400.css";
import "@fontsource/be-vietnam-pro/latin-500.css";
import "@fontsource/be-vietnam-pro/vietnamese-500.css";
import "@fontsource/be-vietnam-pro/latin-700.css";
import "@fontsource/be-vietnam-pro/vietnamese-700.css";
import "@fontsource/be-vietnam-pro/latin-800.css";
import "@fontsource/be-vietnam-pro/vietnamese-800.css";
import App from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
