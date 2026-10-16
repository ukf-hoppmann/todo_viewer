import { useStorageInfo } from "../../api/queries";
import { describeError, useI18n } from "../../i18n/i18n";
import { BACKENDS } from "../../state/uiState";
import { useUiState } from "../../state/useUiStateStore";
import { NotesSettings } from "./NotesSettings";

/** The central database (read-only) and the storage new projects start with. */
export function GeneralSection() {
  const i18n = useI18n();
  const { t } = i18n;
  const { state, dispatch } = useUiState();
  const storage = useStorageInfo();

  return (
    <div className="settings-section">
      <h4>{t("settings.db.title")}</h4>
      {storage.error ? (
        <div className="modal-error">{t("settings.db.failed", { e: describeError(i18n, storage.error) })}</div>
      ) : !storage.data ? (
        <div className="hint">{t("settings.db.loading")}</div>
      ) : (
        <dl className="settings-facts">
          <dt>{t("settings.db.kind")}</dt>
          <dd>{storage.data.kind}</dd>
          <dt>{t("settings.db.location")}</dt>
          <dd className="mono">{storage.data.location}</dd>
          <dt>{t("settings.db.version")}</dt>
          <dd>{storage.data.schema_version}</dd>
        </dl>
      )}
      <p className="hint">{t("settings.db.hint")}</p>

      <h4 id="settings-default-backend">{t("settings.defaultBackend")}</h4>
      <div className="backend-choice" role="radiogroup" aria-labelledby="settings-default-backend">
        {BACKENDS.map((backend) => (
          <label key={backend}>
            <input
              type="radio"
              name="default-backend"
              checked={state.defaultBackend === backend}
              onChange={() => dispatch({ type: "defaultBackend", backend })}
            />
            {t(`source.backend.${backend}`)}
          </label>
        ))}
      </div>
      <p className="hint">{t("settings.defaultBackend.hint")}</p>

      <NotesSettings />
    </div>
  );
}
