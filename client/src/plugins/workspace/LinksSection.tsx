import CloseIcon from "@mui/icons-material/Close";
import { Box, Button, IconButton, MenuItem, Stack, TextField, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { EntityPicker, type Entity } from "../../shared";
import {
	errorMessage,
	useAddLinkMutation,
	useListLinksQuery,
	useRemoveLinkMutation,
	useSearchElementsQuery,
	type LinkedElement,
	type LinkRole,
} from "./api";
import { workspaceTestIds } from "./testIds";

interface Props {
	/** The element whose links are shown. */
	elementUid: string;
	/** Hides the controls to add and remove (a read-only view). */
	readOnly?: boolean;
}

const roles: Exclude<LinkRole, "trigger">[] = ["reference", "origin"];

/**
 * The section "Links" of a detail panel: what the element points to and what points to it, with the role.
 * An element in the trash stays in the list, struck through. The role `trigger` belongs to a trigger of the
 * notes: it is shown, but neither added nor removed here. Plugins build this into their detail panels.
 */
export function LinksSection({ elementUid, readOnly = false }: Props) {
	const { t } = useTranslation("workspace");
	const { data } = useListLinksQuery(elementUid);
	const [remove] = useRemoveLinkMutation();

	return (
		<Stack spacing={1} data-testid={workspaceTestIds.links}>
			<LinkList title={t("links.outgoing")} entries={data?.outgoing ?? []} testId={workspaceTestIds.linksOutgoing} onRemove={readOnly ? undefined : (uid) => void remove(uid)} />
			<LinkList title={t("links.incoming")} entries={data?.incoming ?? []} testId={workspaceTestIds.linksIncoming} />
			{!readOnly && <AddLink elementUid={elementUid} />}
		</Stack>
	);
}

function LinkList({ title, entries, testId, onRemove }: { title: string; entries: LinkedElement[]; testId: string; onRemove?: (uid: string) => void }) {
	const { t } = useTranslation("workspace");
	return (
		<Box data-testid={testId}>
			<Typography variant="caption" color="text.secondary">
				{title}
			</Typography>
			{entries.length === 0 && (
				<Typography variant="body2" color="text.secondary">
					{t("links.none")}
				</Typography>
			)}
			{entries.map((entry) => (
				<Box key={entry.link_uid} data-testid={workspaceTestIds.link(entry.link_uid)} sx={{ display: "flex", alignItems: "center", gap: 1 }}>
					<Typography
						variant="body2"
						sx={{ flexGrow: 1, textDecoration: entry.deleted ? "line-through" : undefined }}
						data-deleted={entry.deleted}
					>
						{entry.label}
						{entry.title ? ` — ${entry.title}` : ""}
					</Typography>
					<Typography variant="caption" color="text.secondary">
						{t(`links.roles.${entry.role}`)}
						{entry.deleted ? ` · ${t("links.deleted")}` : ""}
					</Typography>
					{onRemove && entry.role !== "trigger" && (
						<IconButton size="small" aria-label={t("links.remove", { label: entry.label })} onClick={() => onRemove(entry.link_uid)} data-testid={workspaceTestIds.linkRemove(entry.link_uid)}>
							<CloseIcon fontSize="small" />
						</IconButton>
					)}
				</Box>
			))}
		</Box>
	);
}

function AddLink({ elementUid }: { elementUid: string }) {
	const { t } = useTranslation("workspace");
	const [role, setRole] = useState<LinkRole>("reference");
	const [query, setQuery] = useState("");
	const [target, setTarget] = useState<string | null>(null);
	const [error, setError] = useState<string>();
	const { data: found = [] } = useSearchElementsQuery(query, { skip: query.trim() === "" });
	const [add] = useAddLinkMutation();
	const options: Entity[] = found.map((element) => ({ id: element.uid, label: element.label, title: element.title }));

	const submit = async () => {
		if (!target) return;
		setError(undefined);
		const result = await add({ from_uid: elementUid, to_uid: target, role });
		if ("error" in result) setError(errorMessage(result.error, t("links.failed")));
		else {
			setTarget(null);
			setQuery("");
		}
	};

	return (
		<Box>
			<Stack direction="row" spacing={1} sx={{ alignItems: "flex-start" }}>
				<TextField
					select
					size="small"
					label={t("links.role")}
					value={role}
					onChange={(event) => setRole(event.target.value as LinkRole)}
					sx={{ minWidth: 140 }}
					slotProps={{ htmlInput: { "data-testid": workspaceTestIds.linkRole } }}
				>
					{roles.map((value) => (
						<MenuItem key={value} value={value}>
							{t(`links.roles.${value}`)}
						</MenuItem>
					))}
				</TextField>
				<Box sx={{ flexGrow: 1 }}>
					<EntityPicker
						label={t("links.target")}
						options={options}
						disabledIds={[elementUid]}
						noOptionsText={t("links.noMatch")}
						value={target}
						onChange={setTarget}
						onInputChange={setQuery}
					/>
				</Box>
				<Button variant="outlined" disabled={!target} onClick={() => void submit()} data-testid={workspaceTestIds.linkAdd}>
					{t("links.add")}
				</Button>
			</Stack>
			{error && (
				<Typography color="error" variant="body2" role="alert" data-testid={workspaceTestIds.linkError}>
					{error}
				</Typography>
			)}
		</Box>
	);
}
