import React from "react";
import ReactDOM from "react-dom/client";
// Be Vietnam Pro carries the whole product. It is drawn for Vietnamese by a
// Vietnamese foundry, and the argument this product makes is about Vietnamese
// medical language, so the letterforms should be too.
//
// Geist used to carry the tool surfaces. Eight more faces shipped on every
// route for a second visual system that the print world replaced — and because
// Geist is itself a font-display: swap face, a page waiting on Be Vietnam Pro
// fell back to another loading font and reflowed twice. Deleted.
//
// Vietnamese subset first per weight so it wins the match; latin backfills.
// 400 body, 500 document rows and labels, 700 tool headings, 800 display.
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
