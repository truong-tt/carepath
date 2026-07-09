import type { RefObject } from "react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

interface MotionEnhancerProps {
  scope: RefObject<HTMLDivElement | null>;
}

export default function MotionEnhancer({ scope }: MotionEnhancerProps) {
  useGSAP(
    () => {
      gsap.utils.toArray<HTMLElement>(".motion-panel").forEach((panel) => {
        gsap.fromTo(
          panel,
          { scale: 0.88 },
          {
            scale: 1,
            ease: "none",
            scrollTrigger: {
              trigger: panel,
              start: "top 92%",
              end: "center 55%",
              scrub: 0.7,
            },
          },
        );
      });

      gsap.fromTo(
        ".safety-card",
        { y: 90 },
        {
          y: 0,
          stagger: 0.09,
          ease: "power2.out",
          scrollTrigger: {
            trigger: ".safety-grid",
            start: "top 80%",
            end: "bottom 70%",
            scrub: 0.8,
          },
        },
      );
    },
    { scope },
  );

  return null;
}
