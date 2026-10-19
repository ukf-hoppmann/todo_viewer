import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import RepeatIcon from "@mui/icons-material/Repeat";
import SnoozeIcon from "@mui/icons-material/Snooze";
import { Box, Chip, IconButton, Stack, Tooltip, Typography } from "@mui/material";
import type { ComponentType, MouseEvent } from "react";
import { useTranslation } from "react-i18next";
import type { DetailAction } from "../../shared";
import type { AlarmOut } from "./api";
import { formatWhen, heading, isFinished, isSeries, waitingFor } from "./model";
import { alarmsTestIds } from "./testIds";

interface Props {
	alarm: AlarmOut;
	selected: boolean;
	expanded: boolean;
	actions: readonly DetailAction[];
	onOpen: () => void;
	onToggle: () => void;
}

/**
 * One reminder in the list: the time, the heading (the text, or the title of its first element) and its elements as
 * chips; closed elements are greyed out. A finished or expired reminder is greyed out and says when it goes. A click
 * opens it in the detail column; the arrow shows the full heading.
 */
export function AlarmCard({ alarm, selected, expanded, actions, onOpen, onToggle }: Props) {
	const { t, i18n } = useTranslation("alarms");
	const finished = isFinished(alarm);
	const stop = (event: MouseEvent) => event.stopPropagation();
	const toggleLabel = expanded ? t("action.collapse") : t("action.expand");
	const repeatLabel = t("repeatTooltip", { repeat: t(`repeat.${alarm.repeat}`) });
	return (
		<Box
			data-testid={alarmsTestIds.row(alarm.uid)}
			data-status={alarm.status}
			aria-selected={selected}
			onClick={onOpen}
			sx={{
				display: "flex",
				gap: 1.5,
				px: 1,
				py: 1,
				borderBottom: 1,
				borderColor: "divider",
				opacity: finished ? 0.6 : 1,
				cursor: "pointer",
				bgcolor: selected ? "action.selected" : undefined,
				"&:hover": { bgcolor: "action.hover" },
			}}
		>
			<Box sx={{ flexGrow: 1, minWidth: 0 }}>
				<Typography variant="caption" color={alarm.status === "Due" ? "warning.main" : "text.secondary"} sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
					{formatWhen(waitingFor(alarm), i18n.language)}
					{alarm.status === "Snoozed" && <SnoozeIcon sx={{ fontSize: 14 }} titleAccess={t("status.Snoozed")} />}
					{isSeries(alarm) && (
						<Tooltip title={repeatLabel}>
							<RepeatIcon sx={{ fontSize: 14 }} aria-label={repeatLabel} data-testid={alarmsTestIds.repeat(alarm.uid)} />
						</Tooltip>
					)}
					{alarm.missed > 0 && (
						<Chip size="small" color="warning" variant="outlined" label={t("missed", { count: alarm.missed })} data-testid={alarmsTestIds.missed(alarm.uid)} sx={{ height: 18, fontSize: 11 }} />
					)}
				</Typography>
				<Typography
					variant="body2"
					data-testid={alarmsTestIds.text(alarm.uid)}
					sx={{ fontWeight: 500, ...(expanded ? {} : { display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }) }}
				>
					{heading(alarm)}
				</Typography>
				{alarm.targets.length > 0 && (
					<Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5, mt: 0.5 }}>
						{alarm.targets.map((target, index) => (
							<Chip
								key={target.uid}
								size="small"
								variant="outlined"
								// Ohne eigenen Text ist der Titel des ersten Elements schon die Überschrift.
								label={!alarm.text && index === 0 ? target.label : `${target.label} — ${target.title}`}
								data-testid={alarmsTestIds.targetChip(alarm.uid, target.uid)}
								data-open={target.open}
								sx={{ maxWidth: "100%", opacity: target.open ? 1 : 0.5, textDecoration: target.open ? undefined : "line-through" }}
							/>
						))}
					</Box>
				)}
				{finished && alarm.purge_at && (
					<Typography variant="caption" color="text.secondary" component="div" sx={{ mt: 0.5 }}>
						{t(`finished.${alarm.status}`, { when: formatWhen(alarm.purge_at, i18n.language) })}
					</Typography>
				)}
			</Box>
			<Stack direction="row" sx={{ flexShrink: 0, alignSelf: "flex-start" }} onClick={stop}>
				<Tooltip title={toggleLabel}>
					<IconButton size="small" aria-label={toggleLabel} aria-expanded={expanded} onClick={onToggle} data-testid={alarmsTestIds.action("expand", alarm.uid)}>
						<ExpandMoreIcon fontSize="small" sx={{ transform: expanded ? "rotate(180deg)" : undefined, transition: "transform 0.2s" }} />
					</IconButton>
				</Tooltip>
				{actions.map(({ id, label, icon, onClick }) => {
					const Icon = icon as ComponentType<{ fontSize?: "small" }>;
					return (
						<Tooltip key={id} title={label}>
							<IconButton size="small" aria-label={label} onClick={onClick} data-testid={alarmsTestIds.action(id, alarm.uid)}>
								<Icon fontSize="small" />
							</IconButton>
						</Tooltip>
					);
				})}
			</Stack>
		</Box>
	);
}
