import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import type { RefObject } from "react";

gsap.registerPlugin(useGSAP, ScrollTrigger);

export function useLandingMotion(scope: RefObject<HTMLElement>) {
  useGSAP(
    () => {
      const media = gsap.matchMedia();

      media.add(
        "(min-width: 1024px) and (prefers-reduced-motion: no-preference)",
        () => {
          const story = scope.current?.querySelector<HTMLElement>(
            "[data-product-story]",
          );
          const rail = story?.querySelector<HTMLElement>("[data-product-index]");

          if (story && rail) {
            ScrollTrigger.create({
              trigger: story,
              endTrigger: story,
              start: "top top+=96",
              end: "bottom bottom-=96",
              pin: rail,
              pinSpacing: false,
              invalidateOnRefresh: true,
            });
          }

        },
      );

      return () => media.revert();
    },
    { scope },
  );
}
