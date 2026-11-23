import { Box, FormControlLabel, MenuItem, Switch, TextField } from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { EditForm, EntityPicker, type Entity } from "../../shared";
import { toWriteError, useGetItemQuery, useListItemsQuery, type ItemOut } from "./api";
import { PRIORITIES } from "./constants";
import { useItemWrite } from "./useItemWrite";
import { backlogTestIds } from "./testIds";

interface Props {
	projectUid: string;
	/** The type of a new item; an existing item keeps its type (change it with the type dialog). */
	type: string;
	/** The item to edit; a new one is created if missing. */
	item?: ItemOut;
	/** The parent of a new item ("create child"). */
	parentUid?: string | null;
	onDone: () => void;
	onCancel: () => void;
}

/**
 * The form to create or edit an item. Title, goal and completion criteria are required. Saving sends only what changed when editing, and a version
 * conflict offers to load the current state.
 */
export function ItemForm({ projectUid, type, item, parentUid = null, onDone, onCancel }: Props) {
	const { t } = useTranslation("backlog");
	const write = useItemWrite();
	const { data: all = [] } = useListItemsQuery([projectUid]);
	const { refetch: refetchItem } = useGetItemQuery(item?.uid ?? "", { skip: !item });
	const [title, setTitle] = useState(item?.title ?? "");
	const [priority, setPriority] = useState(item?.priority ?? "Normal");
	const [goal, setGoal] = useState(item?.goal ?? "");
	const [criteria, setCriteria] = useState(item?.completion_criteria ?? "");
	const [summary, setSummary] = useState(item?.summary ?? "");
	const [parent, setParent] = useState<string | null>(item ? (item.parent?.uid ?? null) : parentUid);
	const [required, setRequired] = useState<boolean>(item?.required_for_parent ?? true);
	const [dependencies, setDependencies] = useState<string[]>(item?.dependencies.map((d) => d.uid) ?? []);

	const options: Entity[] = useMemo(() => all.map((entry) => ({ id: entry.uid, label: entry.label, title: entry.title })), [all]);
	const parents = useMemo(() => options.filter((option) => all.find((entry) => entry.uid === option.id)?.type !== "Task"), [options, all]);

	const save = async () => {
		try {
			if (item) {
				const fields: Record<string, unknown> = { title, priority, goal, completion_criteria: criteria, summary, parent, dependencies };
				if (parent) fields.required_for_parent = required;
				await write.updateItem({ uid: item.uid, version: item.version }, fields);
			} else {
				const fields: Record<string, unknown> = { title, priority, goal, completion_criteria: criteria, dependencies };
				if (summary.trim()) fields.summary = summary;
				if (parent) {
					fields.parent = parent;
					fields.required_for_parent = required;
				}
				await write.createItem(projectUid, type, fields);
			}
		} catch (failure) {
			throw toWriteError(failure);
		}
		onDone();
	};

	return (
		<Box data-testid={backlogTestIds.form}>
			<EditForm
				onSave={save}
				onCancel={onCancel}
				// The caller keys the form by the version of the item, so loading the current state resets it.
				onReload={async () => {
					await refetchItem();
				}}
				labels={{ save: t("form.save"), cancel: t("form.cancel"), conflict: t("form.conflict"), reload: t("form.reload") }}
			>
				<TextField label={t("field.title")} value={title} onChange={(event) => setTitle(event.target.value)} required size="small" autoFocus slotProps={{ htmlInput: { "data-testid": backlogTestIds.formField("title") } }} />
				<TextField select size="small" label={t("field.priority")} value={priority} onChange={(event) => setPriority(event.target.value)} slotProps={{ htmlInput: { "data-testid": backlogTestIds.formField("priority") } }}>
					{PRIORITIES.map((value) => (
						<MenuItem key={value} value={value}>
							{t(`priority.${value}`)}
						</MenuItem>
					))}
				</TextField>
				<TextField label={t("field.goal")} value={goal} onChange={(event) => setGoal(event.target.value)} required multiline minRows={2} size="small" slotProps={{ htmlInput: { "data-testid": backlogTestIds.formField("goal") } }} />
				<TextField label={t("field.completionCriteria")} value={criteria} onChange={(event) => setCriteria(event.target.value)} required multiline minRows={2} size="small" slotProps={{ htmlInput: { "data-testid": backlogTestIds.formField("completion_criteria") } }} />
				<TextField label={t("field.summary")} value={summary} onChange={(event) => setSummary(event.target.value)} multiline size="small" slotProps={{ htmlInput: { "data-testid": backlogTestIds.formField("summary") } }} />
				{type !== "Epic" && (
					<>
						<EntityPicker label={t("field.parent")} options={parents} disabledIds={item ? [item.uid] : []} value={parent} onChange={setParent} />
						{parent && (
							<FormControlLabel
								control={<Switch checked={required} onChange={(event) => setRequired(event.target.checked)} slotProps={{ input: { "data-testid": backlogTestIds.formField("required") } as never }} />}
								label={t("field.requiredForParent")}
							/>
						)}
					</>
				)}
				<EntityPicker multiple label={t("field.dependencies")} options={options} disabledIds={item ? [item.uid] : []} value={dependencies} onChange={setDependencies} />
			</EditForm>
			{write.dialog}
		</Box>
	);
}
