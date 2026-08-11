// Authored icons for the visit surface. One family, 24-unit grid, 1.75 stroke,
// round caps and joins — so a chip, a button and a warning read as one system.
// Emoji were used here first and looked consumer-grade next to clinical content.

import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement> & { title?: string };

function Icon({ title, children, ...props }: IconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="1em"
      height="1em"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden={title ? undefined : true}
      role={title ? "img" : undefined}
      focusable="false"
      {...props}
    >
      {title ? <title>{title}</title> : null}
      {children}
    </svg>
  );
}

/** Capsule on the diagonal — medication. */
export const PillIcon = (p: IconProps) => (
  <Icon {...p}>
    <rect x="2.6" y="8.6" width="18.8" height="6.8" rx="3.4" transform="rotate(-45 12 12)" />
    <path d="M9.2 6.8 17.2 14.8" />
  </Icon>
);

/** Balance beam — dose. */
export const DoseIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M12 4v16M7 20h10M4 8h16M6.4 8l-2.6 5.2a3 3 0 0 0 5.2 0Z" />
    <path d="M17.6 8l-2.6 5.2a3 3 0 0 0 5.2 0Z" />
  </Icon>
);

/** Closed loop with a tick — frequency. */
export const RepeatIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M4 9a6 6 0 0 1 6-6h8m0 0-3-3m3 3-3 3" />
    <path d="M20 15a6 6 0 0 1-6 6H6m0 0 3 3m-3-3 3-3" />
  </Icon>
);

/** Triangle with a bar — allergy and other critical flags. */
export const AlertIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M12 3.6 22 20H2Z" />
    <path d="M12 10v4M12 17h.01" />
  </Icon>
);

/** Sheet with ruled lines — a document. */
export const DocumentIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8Z" />
    <path d="M14 3v5h5M8.5 13h7M8.5 16.5h4.5" />
  </Icon>
);

/** Lens and body — capture. */
export const CameraIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M3 8.5A2 2 0 0 1 5 6.5h2.2l1.3-2h7l1.3 2H19a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z" />
    <circle cx="12" cy="13" r="3.4" />
  </Icon>
);

/** Two-way arrows — route of administration. */
export const DropIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M12 3.5c3.4 4 5.5 6.7 5.5 9.2a5.5 5.5 0 0 1-11 0c0-2.5 2.1-5.2 5.5-9.2Z" />
  </Icon>
);

/** Crossed circle — negation. */
export const NoIcon = (p: IconProps) => (
  <Icon {...p}>
    <circle cx="12" cy="12" r="8.5" />
    <path d="M6.2 6.2 17.8 17.8" />
  </Icon>
);

/** Pin — body location. */
export const PinIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M12 21s7-5.6 7-11a7 7 0 1 0-14 0c0 5.4 7 11 7 11Z" />
    <circle cx="12" cy="10" r="2.6" />
  </Icon>
);

/** Descending bar — low confidence. */
export const GaugeIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M3.5 18a8.5 8.5 0 0 1 17 0" />
    <path d="M12 18l4.2-4.6" />
  </Icon>
);

/** Left/right arrows — laterality. */
export const SidesIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M8 7 4 12l4 5M16 7l4 5-4 5M12 4v16" />
  </Icon>
);

/** Clipboard — history, diagnosis, general clinical note. */
export const ClipboardIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M9 4.5H7a2 2 0 0 0-2 2V19a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V6.5a2 2 0 0 0-2-2h-2" />
    <rect x="9" y="2.8" width="6" height="3.4" rx="1.2" />
    <path d="M8.8 12h6.4M8.8 15.6h4" />
  </Icon>
);

/** Speech marks — pronoun and conversational cues. */
export const SpeechIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M20 14.5a2.5 2.5 0 0 1-2.5 2.5H9l-4 3.5V6.5A2.5 2.5 0 0 1 7.5 4h10A2.5 2.5 0 0 1 20 6.5Z" />
  </Icon>
);

export const SpinnerIcon = (p: IconProps) => (
  <Icon {...p} className={`visit-spin ${p.className ?? ""}`.trim()}>
    <path d="M12 3.5a8.5 8.5 0 1 0 8.5 8.5" />
  </Icon>
);
