import { useEffect, useRef, useState } from "react";
import LandingPage from "./LandingPage";
import DemoHub from "./demo/DemoHub";
import ScribeTool from "./scribe/ScribeTool";
import VisitScreen from "./visit/VisitScreen";

const CLINICAL_NOTES_PATH = "/ghi-chep-lam-sang/";
const VISIT_PATH = "/kham-song-ngu/";
const DEMO_PATH = "/thu-nghiem/";

export default function App() {
  const [pathname, setPathname] = useState(() => window.location.pathname);
  const wasScribeTool = useRef(false);

  // index.html is the single source of truth for the title and description.
  // This used to overwrite both from strings.ts on mount, which still carried
  // "Bớt gõ bệnh án" from the retired Scribe-led site — so the served page
  // announced the previous product while the h1 described this one. The tab
  // title also has to be right before JS runs, for a share and for a crawler.
  useEffect(() => {
    document.documentElement.lang = "vi";
  }, []);

  useEffect(() => {
    if (window.location.hash === "#/scribe" || pathname === "/ghi-chep-lam-sang") {
      window.history.replaceState(null, "", CLINICAL_NOTES_PATH);
      setPathname(CLINICAL_NOTES_PATH);
    }
    if (pathname === "/kham-song-ngu") {
      window.history.replaceState(null, "", VISIT_PATH);
      setPathname(VISIT_PATH);
    }
    if (pathname === "/thu-nghiem") {
      window.history.replaceState(null, "", DEMO_PATH);
      setPathname(DEMO_PATH);
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
  const isVisit = pathname === VISIT_PATH;
  const isDemo = pathname === DEMO_PATH;

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

  if (isVisit) return <VisitScreen backHref="/" />;
  if (isDemo) return <DemoHub backHref="/" />;
  return isScribeTool ? (
    <ScribeTool backHref="/" />
  ) : (
    <LandingPage />
  );
}
