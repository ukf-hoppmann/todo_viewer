import { type ReactNode, useEffect } from "react";
import { usePausePolling } from "../state/pollingPause";

interface ModalProps {
  labelledBy: string;
  onDismiss: () => void;
  className?: string;
  children: ReactNode;
}

/** Dialog shell: Escape or a click on the backdrop dismisses; polling pauses while open. */
export function Modal({ labelledBy, onDismiss, className = "", children }: ModalProps) {
  usePausePolling(true);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onDismiss();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onDismiss]);

  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onDismiss()}>
      <div className={`modal ${className}`} role="dialog" aria-modal="true" aria-labelledby={labelledBy}>
        {children}
      </div>
    </div>
  );
}
