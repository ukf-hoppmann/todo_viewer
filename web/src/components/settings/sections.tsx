import type { ComponentType } from "react";
import type { MessageKey } from "../../i18n/messages";
import { GeneralSection } from "./GeneralSection";

export interface SettingsSection {
  id: string;
  titleKey: MessageKey;
  Component: ComponentType;
}

/** The sections of the settings dialog, in order. A new section is a new entry here and nothing else. */
export const SETTINGS_SECTIONS: readonly SettingsSection[] = [{ id: "general", titleKey: "settings.general", Component: GeneralSection }];
