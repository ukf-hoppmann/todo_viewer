import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import SwapHorizIcon from "@mui/icons-material/SwapHoriz";
import { Box, Chip, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useSlot } from "../../core";
import { DetailField, DetailPanel, DetailSection, InlineField, MarkdownView, type DetailAction } from "../../shared";
import { DetailSections, LinksSection, useDeleteElement } from "../workspace";
import { useGetItemQuery, useListItemsQuery, type ItemOut, type ItemSummary } from "./api";
import { PRIORITIES, STATUSES, defaultResolution, statusColor } from "./constants";
import { DocumentsSection } from "./DocumentsSection";
import { ItemDetailState } from "./itemDetailContext";
import { ItemFormDialog, RetypeDialog, RetypeNotice, type RetypeResult } from "./ItemDialogs";
import { TextPromptDialog } from "./TextPromptDialog";
import { backlogTestIds } from "./testIds";
import { useItemWrite } from "./useItemWrite";

interface Props {
	uid: string;
	onSelect: (uid: string) => void;
	/** Shows a close button in the header. */
	onClose?: () => void;
}

/**
 * The detail panel of an item: all fields, its parent, children (also those in the trash) and dependencies.
 * Status, priority, "required for parent" and dependencies change at once; the form edits everything
 * else; the buttons create a child, change the type and move the item to the trash.
 */
export function ItemDetail({ uid, onSelect, onClose }: Props) {
	const { t } = useTranslation("backlog");
	const { data: item, isError } = useGetItemQuery(uid);

	if (isError) return <Typography color="error" sx={{ p: 2 }}>{t("detail.failed")}</Typography>;
	if (!item) return null;
	return <Loaded item={item} onSelect={onSelect} onClose={onClose} />;
}

function Loaded({ item, onSelect, onClose }: { item: ItemOut; onSelect: (uid: string) => void; onClose?: () => void }) {
	const { t } = useTranslation("backlog");
	const write = useItemWrite();
	const trash = useDeleteElement();
	const { data: siblings = [] } = useListItemsQuery([item.project_uid]);
	const [dialog, setDialog] = useState<"edit" | "child" | "retype" | undefined>();
	const [notice, setNotice] = useState<RetypeResult>();
	const [prompt, setPrompt] = useState<"resolution">();
	const [pendingStatus, setPendingStatus] = useState<string>();
	const widgets = useSlot("backlog.item-detail");

	const save = (fields: Record<string, unknown>, resolution?: string) => write.updateItem(item, fields, resolution).then(() => undefined);
	const text = (name: string, label: string, value: string | null | undefined) =>
		value ? (
			<DetailField id={name} label={label}>
				<span data-testid={backlogTestIds.field(name)}>
					<MarkdownView source={value} outlineLabel={t("documents.toc")} />
				</span>
			</DetailField>
		) : null;

	const actions: DetailAction[] = item.deleted
		? []
		: [
				{ id: "edit", label: t("action.edit"), icon: EditIcon, onClick: () => setDialog("edit") },
				{ id: "child", label: t("action.addChild"), icon: AddIcon, onClick: () => setDialog("child"), disabled: item.type === "Task" },
				{ id: "retype", label: t("action.retype"), icon: SwapHorizIcon, onClick: () => setDialog("retype") },
				{ id: "delete", label: t("action.delete"), icon: DeleteIcon, onClick: () => void trash.requestDelete(item.uid, item.version) },
			];
	const options = (values: readonly string[], prefix: string) => values.map((value) => ({ value, label: t(`${prefix}.${value}`) }));

	return (
		<Box data-testid={backlogTestIds.detail}>
			<DetailPanel title={`${item.label} — ${item.title}`} subtitle={item.deleted ? t("detail.deleted") : t(`type.${item.type}`)} actions={actions} onClose={onClose} closeLabel={t("form.close")}>
				{trash.failed && <Typography color="error" variant="body2">{trash.failed}</Typography>}
				{item.deleted ? (
					<DetailField id="status" label={t("field.status")}>
						<Chip size="small" label={t(`status.${item.status}`)} sx={{ bgcolor: statusColor(item.status), color: "common.white" }} data-testid={backlogTestIds.field("status")} />
					</DetailField>
				) : (
					<>
						<InlineField
							id="status"
							kind="select"
							label={t("field.status")}
							value={item.status}
							options={options(STATUSES, "status")}
							onSave={(status) => {
								if (status === "Completed" || status === "Rejected") {
									setPendingStatus(status);
									setPrompt("resolution");
									return;
								}
								return save({ status });
							}}
						/>
						<InlineField id="priority" kind="select" label={t("field.priority")} value={item.priority} options={options(PRIORITIES, "priority")} onSave={(priority) => save({ priority })} />
						{item.parent && (
							<InlineField
								id="required"
								kind="select"
								label={t("field.requiredForParent")}
								value={item.required_for_parent === false ? "no" : "yes"}
								options={[
									{ value: "yes", label: t("detail.yes") },
									{ value: "no", label: t("detail.no") },
								]}
								onSave={(value) => save({ required_for_parent: value === "yes" })}
							/>
						)}
						<InlineField
							id="dependencies"
							kind="multiselect"
							label={t("field.dependencies")}
							value={item.dependencies.map((dependency) => dependency.uid)}
							options={siblings.filter((entry) => entry.uid !== item.uid).map((entry) => ({ value: entry.uid, label: `${entry.label} — ${entry.title}` }))}
							onSave={(dependencies) => save({ dependencies })}
						/>
					</>
				)}
				<DetailField id="created" label={t("field.created")}>
					<span data-testid={backlogTestIds.field("created")}>{item.created}</span>
				</DetailField>
				{item.parent && (
					<DetailField id="parent" label={t("field.parent")}>
						<SummaryLink summary={item.parent} onSelect={onSelect} testId={backlogTestIds.parent} />
						{item.required_for_parent === false && <Chip size="small" variant="outlined" label={t("detail.optional")} sx={{ ml: 1 }} />}
					</DetailField>
				)}
				{text("goal", t("field.goal"), item.goal)}
				{text("completion_criteria", t("field.completionCriteria"), item.completion_criteria)}
				{text("summary", t("field.summary"), item.summary)}
				{text("resolution", t("field.resolution"), item.resolution)}
				{item.progress && (
					<DetailField id="progress" label={t("field.progress")}>
						<span data-testid={backlogTestIds.field("progress")}>
							{item.progress.done}/{item.progress.total}
						</span>
					</DetailField>
				)}
				{item.dependencies.length > 0 && (
					<DetailSection id="dependencies" title={t("field.dependencies")}>
						{item.dependencies.map((dependency) => (
							<SummaryLink key={dependency.uid} summary={dependency} onSelect={onSelect} testId={backlogTestIds.dependency(dependency.uid)} />
						))}
					</DetailSection>
				)}
				{item.children.length > 0 && (
					<DetailSection id="children" title={t("field.children")}>
						{item.children.map((child) => (
							<SummaryLink key={child.uid} summary={child} onSelect={onSelect} testId={backlogTestIds.child(child.uid)} />
						))}
					</DetailSection>
				)}
				{widgets.length > 0 && (
					<ItemDetailState.Provider value={item}>
						{widgets.map((entry) => (
							<entry.component key={`${entry.ownerId}/${entry.name}`} />
						))}
					</ItemDetailState.Provider>
				)}
				<DetailSection id="documents" title={t("field.documents")}>
					<DocumentsSection item={item} />
				</DetailSection>
				<DetailSection id="links" title={t("field.links")} defaultOpen={false}>
					<LinksSection elementUid={item.uid} />
				</DetailSection>
				<DetailSections uid={item.uid} label={item.label} projectUid={item.project_uid} />
			</DetailPanel>
			{dialog === "edit" && <ItemFormDialog projectUid={item.project_uid} type={item.type} item={item} onClose={() => setDialog(undefined)} />}
			{dialog === "child" && (
				<ItemFormDialog projectUid={item.project_uid} type={item.type === "Epic" ? "Story" : "Task"} parentUid={item.uid} onClose={() => setDialog(undefined)} />
			)}
			{dialog === "retype" && (
				<RetypeDialog
					item={item}
					onClose={() => setDialog(undefined)}
					onDone={(result) => {
						setDialog(undefined);
						setNotice(result);
					}}
				/>
			)}
			{notice && <RetypeNotice result={notice} onClose={() => setNotice(undefined)} />}
			{prompt === "resolution" && pendingStatus && (
				<TextPromptDialog
					title={t("resolution.title", { label: item.label, status: t(`status.${pendingStatus}`) })}
					label={t("field.resolution")}
					initial={defaultResolution(pendingStatus)}
					multiline
					confirmLabel={t("form.save")}
					cancelLabel={t("form.cancel")}
					onCancel={() => setPrompt(undefined)}
					onSubmit={async (resolution) => {
						await save({ status: pendingStatus }, resolution);
						setPrompt(undefined);
					}}
				/>
			)}
			{write.dialog}
			{trash.dialog}
		</Box>
	);
}

/** A reference to another item: clickable, struck through when it lies in the trash, dashed when optional. */
function SummaryLink({ summary, onSelect, testId }: { summary: ItemSummary; onSelect: (uid: string) => void; testId: string }) {
	const { t } = useTranslation("backlog");
	const optional = summary.required_for_parent === false;
	return (
		<Box
			component="button"
			type="button"
			onClick={() => onSelect(summary.uid)}
			data-testid={testId}
			data-deleted={summary.deleted}
			data-optional={optional}
			sx={{
				display: "flex",
				alignItems: "center",
				gap: 1,
				width: "100%",
				textAlign: "left",
				bgcolor: "transparent",
				color: "inherit",
				cursor: "pointer",
				border: optional || summary.deleted ? "1px dashed" : "1px solid transparent",
				borderColor: "text.disabled",
				borderRadius: 1,
				px: 0.5,
				textDecoration: summary.deleted ? "line-through" : "none",
				opacity: summary.deleted || optional ? 0.7 : 1,
			}}
		>
			<Box sx={{ width: 10, height: 10, borderRadius: "50%", bgcolor: statusColor(summary.status), flexShrink: 0 }} />
			<Typography variant="caption" color="text.secondary">
				{summary.label}
			</Typography>
			<Typography variant="body2" noWrap>
				{summary.title}
			</Typography>
			{summary.deleted && (
				<Typography variant="caption" color="text.secondary" sx={{ ml: "auto" }}>
					{t("detail.deletedShort")}
				</Typography>
			)}
		</Box>
	);
}
