import { useState } from "react";
import { useI18n } from "../../i18n/i18n";
import { Modal } from "../Modal";
import { SETTINGS_SECTIONS, type SettingsSection } from "./sections";

interface SettingsDialogProps {
  sections?: readonly SettingsSection[];
  /** The section to open; the first one if unset or unknown. */
  initialSection?: string;
  onClose: () => void;
}

/** Navigation of the sections on the left, the chosen section on the right. */
export function SettingsDialog({ sections = SETTINGS_SECTIONS, initialSection, onClose }: SettingsDialogProps) {
  const { t } = useI18n();
  const [activeId, setActiveId] = useState(initialSection);
  const active = sections.find((s) => s.id === activeId) ?? sections[0];

  return (
    <Modal labelledBy="settings-title" onDismiss={onClose} className="settings-dialog">
      <h3 id="settings-title">{t("settings.title")}</h3>
      <div className="settings-body">
        <nav className="settings-nav" aria-label={t("settings.sections")}>
          {sections.map((section) => (
            <button
              key={section.id}
              className={section.id === active?.id ? "active" : ""}
              aria-current={section.id === active?.id ? "page" : undefined}
              onClick={() => setActiveId(section.id)}
            >
              {t(section.titleKey)}
            </button>
          ))}
        </nav>
        <div className="settings-content">{active && <active.Component />}</div>
      </div>
      <div className="modal-actions">
        <button className="btn" onClick={onClose}>
          {t("close")}
        </button>
      </div>
    </Modal>
  );
}
