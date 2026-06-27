// CarePath landing page — nav state, mobile menu, scroll reveal.
// No scroll-event listeners (IntersectionObserver only). Honors reduced motion.
(() => {
  "use strict";
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---- Sticky nav shadow (sentinel, no scroll listener) ----
  const nav = document.getElementById("lpNav");
  const sentinel = document.getElementById("lp-top-sentinel");
  if (nav && sentinel && "IntersectionObserver" in window) {
    new IntersectionObserver(
      ([entry]) => nav.classList.toggle("is-stuck", !entry.isIntersecting),
      { rootMargin: "-8px 0px 0px 0px" }
    ).observe(sentinel);
  }

  // ---- Mobile menu ----
  const burger = document.getElementById("lpBurger");
  const links = document.getElementById("lpNavLinks");
  if (burger && links) {
    const setOpen = (open) => {
      links.classList.toggle("is-open", open);
      burger.setAttribute("aria-expanded", String(open));
      burger.setAttribute("aria-label", open ? "Đóng menu" : "Mở menu");
    };
    burger.addEventListener("click", () => setOpen(!links.classList.contains("is-open")));
    links.addEventListener("click", (e) => { if (e.target.closest("a")) setOpen(false); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") setOpen(false); });
  }

  // ---- Reveal on scroll ----
  const revs = document.querySelectorAll(".reveal-on-scroll");
  if (reduce || !("IntersectionObserver" in window)) {
    revs.forEach((n) => n.classList.add("is-in"));
  } else {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((en) => {
          if (en.isIntersecting) { en.target.classList.add("is-in"); io.unobserve(en.target); }
        });
      },
      { threshold: 0.14, rootMargin: "0px 0px -8% 0px" }
    );
    revs.forEach((n) => io.observe(n));
  }
})();
