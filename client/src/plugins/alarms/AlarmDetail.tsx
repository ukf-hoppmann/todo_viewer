import { Box, ButtonBase, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { DetailPanel, type DetailAction } from "../../shared";
import { ElementDetail } from "../workspace";
import type { AlarmOut, AlarmTarget } from "./api";
import { formatWhen, heading, waitingFor } from "./model";
import { alarmsTestIds } from "./testIds";

interface Props {
	alarm: AlarmOut;
	actions: readonly DetailAction[];
	onClose: () => void;
}

/**
 * A reminder in the detail column: a bar with time, heading and actions, then what it reminds of. One element is shown
 * directly; several are cards to switch between (the first is open); a free reminder is only the bar. Closed elements
 * are greyed out; one in the trash is not shown. Each element is shown by its owner through `ElementDetail`.
 */
export function AlarmDetail({ alarm, actions, onClose }: Props) {
	const { t, i18n } = useTranslation("alarms");
	const [chosen, setChosen] = useState<string>();
	const current = alarm.targets.find((target) => target.uid === chosen) ?? alarm.targets[0];
	const when = `⏰ ${formatWhen(waitingFor(alarm), i18n.language)}`;
	const status = alarm.status === "Pending" ? "" : t(`status.${alarm.status}`);
	// Ohne eigenen Text ist das Element selbst die Überschrift: die Leiste nennt dann nur Zeit und Zustand.
	const title = alarm.text ? heading(alarm) : when;
	const subtitle = alarm.text ? [when, status].filter(Boolean).join(" · ") : status || undefined;
	return (
		<Box data-testid={alarmsTestIds.detail}>
			<DetailPanel title={title} subtitle={subtitle} actions={actions} onClose={onClose} closeLabel={t("detail.close")} />
			{alarm.targets.length > 1 && (
				<Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, px: 2, pb: 1 }}>
					{alarm.targets.map((target) => (
						<TargetCard key={target.uid} target={target} selected={target.uid === current?.uid} onSelect={() => setChosen(target.uid)} />
					))}
				</Box>
			)}
			{current &&
				(current.deleted ? (
					<Typography color="text.secondary" sx={{ px: 2, py: 1 }}>
						{t("detail.deleted", { label: current.label })}
					</Typography>
				) : (
					<Box sx={{ opacity: current.open ? 1 : 0.6 }}>
						<ElementDetail key={current.uid} uid={current.uid} kind={current.kind} label={current.label} title={current.title} />
					</Box>
				))}
		</Box>
	);
}

function TargetCard({ target, selected, onSelect }: { target: AlarmTarget; selected: boolean; onSelect: () => void }) {
	return (
		<ButtonBase
			onClick={onSelect}
			aria-pressed={selected}
			data-testid={alarmsTestIds.targetCard(target.uid)}
			data-open={target.open}
			sx={{
				display: "block",
				textAlign: "left",
				maxWidth: 220,
				px: 1.25,
				py: 0.75,
				border: 1,
				borderRadius: 1,
				borderColor: selected ? "primary.main" : "divider",
				bgcolor: selected ? "action.selected" : undefined,
				opacity: target.open ? 1 : 0.5,
			}}
		>
			<Typography variant="caption" color="text.secondary" component="div">
				{target.label}
			</Typography>
			<Typography variant="body2" noWrap sx={{ textDecoration: target.open ? undefined : "line-through" }}>
				{target.title}
			</Typography>
		</ButtonBase>
	);
}
