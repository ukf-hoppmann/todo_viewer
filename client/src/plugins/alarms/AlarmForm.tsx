import { Box, TextField } from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { EditForm, EntityPicker, type Entity } from "../../shared";
import { useSearchElementsQuery } from "../workspace";
import { toWriteError, useCreateAlarmMutation, useUpdateAlarmMutation, type AlarmOut } from "./api";
import { fromInputValue, toInputValue } from "./model";
import { alarmsTestIds } from "./testIds";

interface Props {
	projectUid: string;
	/** The alarm to edit; a new one is created if missing. */
	alarm?: AlarmOut;
	/** The element a new alarm is bound to (the detail panel it was started from). */
	targetUid?: string | null;
	onDone: () => void;
	onCancel: () => void;
}

/**
 * The form to set or change an alarm: text, time (local time of the browser) and an optional element it refers to.
 * Saving sends only what changed when editing; a version conflict offers to load the current state.
 */
export function AlarmForm({ projectUid, alarm, targetUid = null, onDone, onCancel }: Props) {
	const { t } = useTranslation("alarms");
	const [create] = useCreateAlarmMutation();
	const [update] = useUpdateAlarmMutation();
	const [text, setText] = useState(alarm?.text ?? "");
	const [at, setAt] = useState(alarm ? toInputValue(alarm.at) : "");
	const [target, setTarget] = useState<string | null>(alarm ? (alarm.target?.uid ?? null) : targetUid);
	const [query, setQuery] = useState("");
	const { data: found = [] } = useSearchElementsQuery(query, { skip: query.trim() === "" });
	const options: Entity[] = useMemo(() => {
		const known = alarm?.target ? [{ id: alarm.target.uid, label: alarm.target.label, title: alarm.target.title }] : [];
		return [...known, ...found.map((element) => ({ id: element.uid, label: element.label, title: element.title }))];
	}, [alarm, found]);

	const save = async () => {
		const iso = fromInputValue(at);
		if (!iso) throw new Error(t("form.timeRequired"));
		try {
			if (alarm) {
				const fields: Record<string, unknown> = {};
				if (text !== alarm.text) fields.text = text;
				if (iso !== new Date(alarm.at).toISOString()) fields.at = iso;
				if (target !== (alarm.target?.uid ?? null)) fields.target = target;
				if (Object.keys(fields).length > 0) await update({ uid: alarm.uid, version: alarm.version, fields }).unwrap();
			} else {
				await create({ project: projectUid, text, at: iso, ...(target ? { target } : {}) }).unwrap();
			}
		} catch (failure) {
			throw toWriteError(failure);
		}
		onDone();
	};

	return (
		<Box data-testid={alarmsTestIds.form}>
			<EditForm
				onSave={save}
				onCancel={onCancel}
				onReload={() => undefined}
				labels={{ save: t("form.save"), cancel: t("form.cancel"), conflict: t("form.conflict"), reload: t("form.reload") }}
			>
				<TextField label={t("field.text")} value={text} onChange={(event) => setText(event.target.value)} required size="small" autoFocus slotProps={{ htmlInput: { "data-testid": alarmsTestIds.formField("text") } }} />
				<TextField
					type="datetime-local"
					label={t("field.at")}
					value={at}
					onChange={(event) => setAt(event.target.value)}
					size="small"
					slotProps={{ inputLabel: { shrink: true }, htmlInput: { "data-testid": alarmsTestIds.formField("at") } }}
				/>
				<EntityPicker label={t("field.target")} options={options} value={target} onChange={setTarget} onInputChange={setQuery} noOptionsText={t("form.searchHint")} />
			</EditForm>
		</Box>
	);
}
