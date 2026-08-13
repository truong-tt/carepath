import { useEffect, useRef, useState } from "react";
import LandingPage from "./LandingPage";
import DemoHub from "./demo/DemoHub";
import GetCareScreen from "./journey/GetCareScreen";
import MyCarePathScreen from "./journey/MyCarePathScreen";
import PaperworkScreen from "./paperwork/PaperworkScreen";
import ScribeTool from "./scribe/ScribeTool";
import VisitScreen from "./visit/VisitScreen";

const CLINICAL_NOTES_PATH = "/ghi-chep-lam-sang/";
const VISIT_PATH = "/kham-song-ngu/";
const DEMO_PATH = "/thu-nghiem/";
const PAPERWORK_PATH = "/dich-giay-to/";
// The patient's two routes are English-slugged: the clinician's tools are named
// in the clinician's language, and these are not the clinician's.
const GET_CARE_PATH = "/get-care/";
const MY_CAREPATH_PATH = "/my-carepath/";

export default function App() {
  const [pathname, setPathname] = useState(() => window.location.pathname);
  const wasScribeTool = useRef(false);

  // index.html is the single source of truth for the title and description.
  // This used to overwrite both from strings.ts on mount, which still carried
  // "Bớt gõ bệnh án" from the retired Scribe-led site — so the served page
  // announced the previous product while the h1 described this one. The tab
  // title also has to be right before JS runs, for a share and for a crawler.
  //
  // The root language is a property of who the route is for, not of the app.
  // The patient's routes are English and the clinic's tools are Vietnamese; the
  // landing page sets its own from the toggle, overriding this on mount.
  useEffect(() => {
    const patientSurface = ["/", GET_CARE_PATH, MY_CAREPATH_PATH].includes(pathname);
    document.documentElement.lang = patientSurface ? "en" : "vi";
  }, [pathname]);

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
    if (pathname === "/dich-giay-to") {
      window.history.replaceState(null, "", PAPERWORK_PATH);
      setPathname(PAPERWORK_PATH);
    }
    if (pathname === "/get-care") {
      window.history.replaceState(null, "", GET_CARE_PATH);
      setPathname(GET_CARE_PATH);
    }
    if (pathname === "/my-carepath") {
      window.history.replaceState(null, "", MY_CAREPATH_PATH);
      setPathname(MY_CAREPATH_PATH);
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
  const isPaperwork = pathname === PAPERWORK_PATH;

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
  if (isPaperwork) return <PaperworkScreen backHref="/" />;
  if (pathname === GET_CARE_PATH) return <GetCareScreen />;
  if (pathname === MY_CAREPATH_PATH) return <MyCarePathScreen />;
  return isScribeTool ? (
    <ScribeTool backHref="/" />
  ) : (
    <LandingPage />
  );
}
