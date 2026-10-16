import { Box, Chip, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { DetailField, DetailPanel, DetailSection, MarkdownView } from "../../shared";
import { LinksSection } from "../workspace";
import { useGetItemQuery, type ItemSummary } from "./api";
import { priorityColor, statusColor } from "./constants";
import { backlogTestIds } from "./testIds";

interface Props {
	uid: string;
	onSelect: (uid: string) => void;
}

/** The detail panel of an item: all fields, its parent, children (also those in the trash) and dependencies. */
export function ItemDetail({ uid, onSelect }: Props) {
	const { t } = useTranslation("backlog");
	const { data: item, isError } = useGetItemQuery(uid);

	if (isError) return <Typography color="error" sx={{ p: 2 }}>{t("detail.failed")}</Typography>;
	if (!item) return null;

	const text = (name: string, label: string, value: string | null | undefined) =>
		value ? (
			<DetailField id={name} label={label}>
				<span data-testid={backlogTestIds.field(name)}>
					<MarkdownView source={value} />
				</span>
			</DetailField>
		) : null;

	return (
		<Box data-testid={backlogTestIds.detail}>
			<DetailPanel title={`${item.label} — ${item.title}`} subtitle={item.deleted ? t("detail.deleted") : t(`type.${item.type}`)}>
				<DetailField id="status" label={t("field.status")}>
					<Chip
						size="small"
						label={t(`status.${item.status}`)}
						sx={{ bgcolor: statusColor(item.status), color: "common.white" }}
						data-testid={backlogTestIds.field("status")}
					/>
				</DetailField>
				<DetailField id="priority" label={t("field.priority")}>
					<Chip
						size="small"
						label={t(`priority.${item.priority}`)}
						sx={{ bgcolor: priorityColor(item.priority), color: "common.white" }}
						data-testid={backlogTestIds.field("priority")}
					/>
				</DetailField>
				<DetailField id="area" label={t("field.area")}>
					<span data-testid={backlogTestIds.field("area")}>{item.area ?? "—"}</span>
				</DetailField>
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
				<DetailSection id="links" title={t("field.links")} defaultOpen={false}>
					<LinksSection elementUid={item.uid} />
				</DetailSection>
			</DetailPanel>
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
