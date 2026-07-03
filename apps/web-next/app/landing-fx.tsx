"use client";

import { useEffect } from "react";

// Port of apps/web/landing.js — nav state, mobile menu, scroll reveal.
// No scroll-event listeners (IntersectionObserver only). Honors reduced motion.
export default function LandingFx() {
  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const cleanups: (() => void)[] = [];

    // ---- Sticky nav shadow (sentinel, no scroll listener) ----
    const nav = document.getElementById("lpNav");
    const sentinel = document.getElementById("lp-top-sentinel");
    if (nav && sentinel && "IntersectionObserver" in window) {
      const navIo = new IntersectionObserver(
        ([entry]) => nav.classList.toggle("is-stuck", !entry.isIntersecting),
        { rootMargin: "-8px 0px 0px 0px" }
      );
      navIo.observe(sentinel);
      cleanups.push(() => navIo.disconnect());
    }

    // ---- Mobile menu ----
    const burger = document.getElementById("lpBurger");
    const links = document.getElementById("lpNavLinks");
    if (burger && links) {
      const setOpen = (open: boolean) => {
        links.classList.toggle("is-open", open);
        burger.setAttribute("aria-expanded", String(open));
        burger.setAttribute("aria-label", open ? "Đóng menu" : "Mở menu");
      };
      const onBurger = () => setOpen(!links.classList.contains("is-open"));
      const onLinks = (e: Event) => {
        if ((e.target as Element).closest("a")) setOpen(false);
      };
      const onKey = (e: KeyboardEvent) => {
        if (e.key === "Escape") setOpen(false);
      };
      burger.addEventListener("click", onBurger);
      links.addEventListener("click", onLinks);
      document.addEventListener("keydown", onKey);
      cleanups.push(() => {
        burger.removeEventListener("click", onBurger);
        links.removeEventListener("click", onLinks);
        document.removeEventListener("keydown", onKey);
      });
    }

    // ---- Reveal on scroll ----
    const revs = document.querySelectorAll(".reveal-on-scroll");
    if (reduce || !("IntersectionObserver" in window)) {
      revs.forEach((n) => n.classList.add("is-in"));
    } else {
      const io = new IntersectionObserver(
        (entries) => {
          entries.forEach((en) => {
            if (en.isIntersecting) {
              en.target.classList.add("is-in");
              io.unobserve(en.target);
            }
          });
        },
        { threshold: 0.14, rootMargin: "0px 0px -8% 0px" }
      );
      revs.forEach((n) => io.observe(n));
      cleanups.push(() => io.disconnect());
    }

    return () => cleanups.forEach((fn) => fn());
  }, []);

  return null;
}
