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

          const cards = Array.from(
            scope.current?.querySelectorAll<HTMLElement>("[data-safety-card]") ?? [],
          );
          const bento = scope.current?.querySelector<HTMLElement>(".safety-bento");
          const sharedCard = cards[0];
          const productCards = cards.slice(1);

          if (bento && sharedCard && productCards.length > 0) {
            gsap.set(cards, { transformOrigin: "center top" });
            gsap.set(sharedCard, { zIndex: 1 });
            gsap.set(productCards, { zIndex: 2 });

            const stack = gsap.timeline({
              scrollTrigger: {
                trigger: bento,
                start: "top 70%",
                end: "bottom 28%",
                scrub: 0.55,
                invalidateOnRefresh: true,
              },
            });
            stack.to(
              sharedCard,
              { autoAlpha: 0.68, ease: "none", scale: 0.965 },
              0,
            );
            productCards.forEach((card) => {
              stack.to(
                card,
                {
                  ease: "none",
                  y: () => -(card.offsetTop - sharedCard.offsetTop) + 18,
                },
                0,
              );
            });
          }

          return () =>
            gsap.set(cards, {
              clearProps: "transform,transformOrigin,opacity,visibility,zIndex",
            });
        },
      );

      return () => media.revert();
    },
    { scope },
  );
}
