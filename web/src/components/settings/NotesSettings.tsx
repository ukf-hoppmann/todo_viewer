import { useState } from "react";
import { useNotesSettings, useSaveNotesSettings } from "../../api/queries";
import { describeError, useI18n } from "../../i18n/i18n";

const DEFAULT_REVIEW_DAYS = 30;
const DEFAULT_MAX_DEPTH = 3;

/** The two options of notes: the review interval and the deepest level of topics. */
export function NotesSettings() {
  const i18n = useI18n();
  const { t } = i18n;
  const settings = useNotesSettings();

  if (settings.error) return <div className="modal-error">{t("settings.notes.failed", { e: describeError(i18n, settings.error) })}</div>;
  if (!settings.data) return null;
  return <NotesSettingsForm reviewDays={settings.data.review_days} maxTopicDepth={settings.data.max_topic_depth} />;
}

/** Starts from the stored values; they are only read when the form opens (a save fills the cache with the new ones). */
function NotesSettingsForm({ reviewDays, maxTopicDepth }: { reviewDays: number; maxTopicDepth: number }) {
  const i18n = useI18n();
  const { t } = i18n;
  const save = useSaveNotesSettings();
  const [days, setDays] = useState(String(reviewDays));
  const [depth, setDepth] = useState(String(maxTopicDepth));

  const submit = () => save.mutate({ review_days: days === "" ? null : Number(days), max_topic_depth: depth === "" ? null : Number(depth) });

  return (
    <form
      className="settings-section"
      aria-label={t("settings.notes.title")}
      onSubmit={(e) => {
        e.preventDefault();
        submit();
      }}
    >
      <h4>{t("settings.notes.title")}</h4>
      <label className="field">
        {t("settings.notes.reviewDays")}
        <input type="number" min={1} max={3650} placeholder={String(DEFAULT_REVIEW_DAYS)} value={days} onChange={(e) => setDays(e.target.value)} />
      </label>
      <p className="hint">{t("settings.notes.reviewDays.hint")}</p>
      <label className="field">
        {t("settings.notes.maxDepth")}
        <input type="number" min={1} max={10} placeholder={String(DEFAULT_MAX_DEPTH)} value={depth} onChange={(e) => setDepth(e.target.value)} />
      </label>
      <p className="hint">{t("settings.notes.maxDepth.hint")}</p>
      {save.error && (
        <div className="field-error" role="alert">
          {t("err.save", { e: describeError(i18n, save.error) })}
        </div>
      )}
      {save.isSuccess && <div className="hint" role="status">{t("settings.notes.saved")}</div>}
      <div className="modal-actions">
        <button type="submit" className="btn primary" disabled={save.isPending}>
          {save.isPending ? t("saving") : t("settings.notes.save")}
        </button>
      </div>
    </form>
  );
}
