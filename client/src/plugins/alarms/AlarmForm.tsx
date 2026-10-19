import { Box, TextField } from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { EditForm, EntityPicker, type Entity } from "../../shared";
import { useSearchElementsQuery } from "../workspace";
import { toWriteError, useCreateAlarmMutation, useUpdateAlarmMutation, type AlarmOut } from "./api";
import { REPEATS, fromInputValue, toInputValue } from "./model";
import { alarmsTestIds } from "./testIds";

interface Props {
	projectUid: string;
	/** The alarm to edit; a new one is created if missing. */
	alarm?: AlarmOut;
	/** The element a new alarm reminds of (the detail panel it was started from). */
	target?: Entity | null;
	onDone: () => void;
	onCancel: () => void;
}

/**
 * The form to set or change a reminder: time (local time of the browser), the elements it reminds of and a text; the
 * text is needed only without elements. Saving sends only what changed when editing; a version conflict offers to load
 * the current state.
 */
export function AlarmForm({ projectUid, alarm, target = null, onDone, onCancel }: Props) {
	const { t } = useTranslation("alarms");
	const [create] = useCreateAlarmMutation();
	const [update] = useUpdateAlarmMutation();
	const [text, setText] = useState(alarm?.text ?? "");
	const [at, setAt] = useState(alarm ? toInputValue(alarm.at) : "");
	const [repeat, setRepeat] = useState<string>(alarm?.repeat ?? "none");
	const initial = alarm ? alarm.targets.map((entry) => entry.uid) : target ? [target.id] : [];
	const [targets, setTargets] = useState<string[]>(initial);
	const [query, setQuery] = useState("");
	const { data: found = [] } = useSearchElementsQuery(query, { skip: query.trim() === "" });
	// What was ever offered stays known, so chosen elements keep their name while the search shows others.
	const [known, setKnown] = useState<Entity[]>(() => (alarm ? alarm.targets.map((entry) => ({ id: entry.uid, label: entry.label, title: entry.title })) : target ? [target] : []));
	const options: Entity[] = useMemo(() => {
		const byId = new Map(known.map((entity) => [entity.id, entity]));
		for (const element of found) byId.set(element.uid, { id: element.uid, label: element.label, title: element.title });
		return [...byId.values()];
	}, [known, found]);
	const choose = (ids: string[]) => {
		setKnown((current) => [...current, ...options.filter((entity) => ids.includes(entity.id) && !current.some((k) => k.id === entity.id))]);
		setTargets(ids);
	};
	const same = (a: readonly string[], b: readonly string[]) => a.length === b.length && a.every((id, index) => id === b[index]);

	const save = async () => {
		const iso = fromInputValue(at);
		if (!iso) throw new Error(t("form.timeRequired"));
		if (!text.trim() && targets.length === 0) throw new Error(t("form.textOrTargets"));
		try {
			if (alarm) {
				const fields: Record<string, unknown> = {};
				if (text !== alarm.text) fields.text = text;
				if (iso !== new Date(alarm.at).toISOString()) fields.at = iso;
				if (repeat !== alarm.repeat) fields.repeat = repeat;
				if (!same(targets, initial)) fields.targets = targets;
				if (Object.keys(fields).length > 0) await update({ uid: alarm.uid, version: alarm.version, fields }).unwrap();
			} else {
				await create({ project: projectUid, text, at: iso, targets, ...(repeat !== "none" ? { repeat } : {}) }).unwrap();
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
				<TextField
					type="datetime-local"
					label={t("field.at")}
					value={at}
					onChange={(event) => setAt(event.target.value)}
					size="small"
					autoFocus
					slotProps={{ inputLabel: { shrink: true }, htmlInput: { "data-testid": alarmsTestIds.formField("at") } }}
				/>
				<TextField
					select
					label={t("field.repeat")}
					value={repeat}
					onChange={(event) => setRepeat(event.target.value)}
					size="small"
					slotProps={{ select: { native: true }, htmlInput: { "data-testid": alarmsTestIds.formField("repeat") } }}
				>
					{REPEATS.map((kind) => (
						<option key={kind} value={kind}>
							{t(`repeat.${kind}`)}
						</option>
					))}
				</TextField>
				<EntityPicker multiple label={t("field.targets")} options={options} value={targets} onChange={choose} onInputChange={setQuery} noOptionsText={t("form.searchHint")} />
				<TextField
					label={t("field.text")}
					helperText={targets.length > 0 ? t("form.textOptional") : undefined}
					value={text}
					onChange={(event) => setText(event.target.value)}
					required={targets.length === 0}
					size="small"
					slotProps={{ htmlInput: { "data-testid": alarmsTestIds.formField("text") } }}
				/>
			</EditForm>
		</Box>
	);
}
