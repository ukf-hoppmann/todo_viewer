import { type ReactNode, useEffect, useRef } from "react";
import { usePausePolling } from "../state/pollingPause";

interface ModalProps {
  labelledBy: string;
  onDismiss: () => void;
  className?: string;
  children: ReactNode;
}

/** The open dialogs, the one on top last: Escape closes only that one. */
const openDialogs: symbol[] = [];

/** Dialog shell: Escape (for the topmost dialog) or a click on the backdrop dismisses; polling pauses while open. */
export function Modal({ labelledBy, onDismiss, className = "", children }: ModalProps) {
  usePausePolling(true);

  // The latest callback, so that a parent passing a new one on every render does not move this dialog in the stack.
  const dismiss = useRef(onDismiss);
  useEffect(() => {
    dismiss.current = onDismiss;
  });

  useEffect(() => {
    const self = Symbol("dialog");
    openDialogs.push(self);
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && openDialogs[openDialogs.length - 1] === self) dismiss.current();
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      openDialogs.splice(openDialogs.indexOf(self), 1);
    };
  }, []);

  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onDismiss()}>
      <div className={`modal ${className}`} role="dialog" aria-modal="true" aria-labelledby={labelledBy}>
        {children}
      </div>
    </div>
  );
}
