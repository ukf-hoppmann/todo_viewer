import type { ReactNode } from "react";

/** 16×16 line icons (stroke only, so they follow the text color). */
const PATHS = {
  edit: "M2 14l1-4 8-8 3 3-8 8-4 1zM9.5 3.5l3 3",
  promote: "M8 13V3M4 7l4-4 4 4",
  done: "M3 8.5l3.5 3.5L13 4.5",
  drop: "M4 4l8 8M12 4l-8 8",
  snooze: "M8 3a5 5 0 100 10A5 5 0 008 3zM8 5.5V8l2 1.5",
  keep: "M4 2h8v12l-4-3-4 3V2z",
  trash: "M3 4h10M6 4V2.5h4V4M4.5 4l.5 9.5h6L11.5 4M7 6.5v5M9 6.5v5",
  plus: "M8 3v10M3 8h10",
  expand: "M9.5 2.5h4v4M6.5 13.5h-4v-4M13.5 2.5L9 7M2.5 13.5L7 9",
  collapse: "M13 6.5H9.5V3M3 9.5h3.5V13M9.5 6.5L14 2M6.5 9.5L2 14",
  close: "M4 4l8 8M12 4l-8 8",
  folderPlus: "M2 4.5h4l1.5 1.5H14v7H2v-8.5zM8 8v3M6.5 9.5h3",
  subfolderPlus: "M3 3v7.5h3M3 6h3M7 8.5h6.5v4.5H7zM10.25 9.8v2M9.25 10.8h2",
  rename: "M2 13h12M4 10l6-6 2 2-6 6H4v-2z",
  calendar: "M3 4h10v9.5H3zM3 7h10M5.5 2.5v3M10.5 2.5v3",
  move: "M2 8h10M9 5l3 3-3 3M13.5 3v10",
  group: "M2.5 3.5h11M5.5 7h8M5.5 10.5h8M8.5 14h5",
  reset: "M3 8a5 5 0 109-3M12 2v3H9",
  restore: "M13 8a5 5 0 11-9-3M4 2v3h3",
  note: "M3 2h7l3 3v9H3V2zM9.5 2v3.5H13M5.5 8.5h5M5.5 11h5",
  spec: "M2.5 13.5l11-11M2.5 13.5v-4l4 4zM5 8l1.5 1.5M7.5 5.5L9 7M10 3l1.5 1.5",
  link: "M6.5 9.5a2.5 2.5 0 003.5 0l2.5-2.5a2.5 2.5 0 00-3.5-3.5L8 4.5M9.5 6.5a2.5 2.5 0 00-3.5 0L3.5 9a2.5 2.5 0 003.5 3.5L8 11.5",
  caretDown: "M4 6l4 4 4-4",
  caretRight: "M6 4l4 4-4 4",
} as const;

export type IconName = keyof typeof PATHS;

export function Icon({ name }: { name: IconName }) {
  return (
    <svg className="icon" viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={PATHS[name]} />
    </svg>
  );
}

interface IconButtonProps {
  icon: IconName;
  /** Hover text and accessible name. */
  label: string;
  onClick: () => void;
  disabled?: boolean;
  variant?: "danger" | "primary";
  pressed?: boolean;
  children?: ReactNode;
}

/** A small square button with an icon; the label is the hover text and the accessible name. */
export function IconButton({ icon, label, onClick, disabled, variant, pressed, children }: IconButtonProps) {
  return (
    <button
      type="button"
      className={`icon-btn${variant ? ` ${variant}` : ""}${pressed ? " active" : ""}`}
      title={label}
      aria-label={label}
      aria-pressed={pressed}
      disabled={disabled}
      onClick={onClick}
    >
      <Icon name={icon} />
      {children}
    </button>
  );
}
