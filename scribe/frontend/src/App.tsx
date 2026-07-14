import { useEffect, useRef, useState } from "react";
import LandingPage from "./LandingPage";
import ScribeTool from "./scribe/ScribeTool";
import { copyFor } from "./content/strings";

const CLINICAL_NOTES_PATH = "/ghi-chep-lam-sang/";

export default function App() {
  const [pathname, setPathname] = useState(() => window.location.pathname);
  const wasScribeTool = useRef(false);

  useEffect(() => {
    document.documentElement.lang = "vi";
    document.title = copyFor("vi").metadata.title;
    document
      .querySelector('meta[name="description"]')
      ?.setAttribute("content", copyFor("vi").metadata.description);
  }, []);

  useEffect(() => {
    if (window.location.hash === "#/scribe" || pathname === "/ghi-chep-lam-sang") {
      window.history.replaceState(null, "", CLINICAL_NOTES_PATH);
      setPathname(CLINICAL_NOTES_PATH);
    }
  }, [pathname]);

  useEffect(() => {
    const onNavigation = () => setPathname(window.location.pathname);
    window.addEventListener("popstate", onNavigation);
    window.addEventListener("hashchange", onNavigation);
    return () => {
      window.removeEventListener("popstate", onNavigation);
      window.removeEventListener("hashchange", onNavigation);
    };
  }, []);

  const isScribeTool = pathname === CLINICAL_NOTES_PATH;

  useEffect(() => {
    if (isScribeTool) window.scrollTo(0, 0);
  }, [isScribeTool]);

  useEffect(() => {
    let frame: number | undefined;
    if (wasScribeTool.current && !isScribeTool) {
      frame = window.requestAnimationFrame(() => {
        const anchor = document.getElementById(window.location.hash.slice(1) || "top") ??
          document.getElementById("top");
        anchor?.scrollIntoView?.();
        anchor?.focus({ preventScroll: true });
      });
    }
    wasScribeTool.current = isScribeTool;
    return () => {
      if (frame !== undefined) window.cancelAnimationFrame(frame);
    };
  }, [isScribeTool]);

  return isScribeTool ? (
    <ScribeTool backHref="/" />
  ) : (
    <LandingPage />
  );
}
