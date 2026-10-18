import CloseIcon from "@mui/icons-material/Close";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { Box, Collapse, IconButton, Tooltip, Typography } from "@mui/material";
import { useState, type ComponentType, type ReactNode } from "react";
import { sharedTestIds } from "./testIds";

export interface DetailAction {
	id: string;
	/** Also the accessible name and the tooltip; translated by the caller. */
	label: string;
	icon: ComponentType;
	onClick: () => void;
	disabled?: boolean;
}

interface DetailPanelProps {
	title: ReactNode;
	subtitle?: ReactNode;
	actions?: readonly DetailAction[];
	/** With a handler the header ends in a close button (`closeLabel` is its translated name). */
	onClose?: () => void;
	closeLabel?: string;
	children?: ReactNode;
}

/** The detail view of one element: a header with the title and close button, a row of icon buttons below it, then the sections. */
export function DetailPanel({ title, subtitle, actions = [], onClose, closeLabel, children }: DetailPanelProps) {
	return (
		<Box data-testid={sharedTestIds.detailPanel} sx={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
			<Box sx={{ p: 1.5, pb: actions.length > 0 ? 0.5 : 1.5, borderBottom: 1, borderColor: "divider" }}>
				<Box sx={{ display: "flex", alignItems: "flex-start", gap: 1 }}>
					<Box sx={{ flexGrow: 1, minWidth: 0 }}>
						<Typography variant="h6" component="h2" sx={{ overflowWrap: "anywhere" }} data-testid={sharedTestIds.detailTitle}>
							{title}
						</Typography>
						{subtitle && (
							<Typography variant="caption" color="text.secondary">
								{subtitle}
							</Typography>
						)}
					</Box>
					{onClose && (
						<Tooltip title={closeLabel}>
							<IconButton aria-label={closeLabel} onClick={onClose} data-testid={sharedTestIds.detailAction("close")}>
								<CloseIcon />
							</IconButton>
						</Tooltip>
					)}
				</Box>
				{actions.length > 0 && (
					<Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5, ml: -1 }}>
						{actions.map(({ id, label, icon: Icon, onClick, disabled }) => (
							<Tooltip key={id} title={label}>
								<span>
									<IconButton aria-label={label} onClick={onClick} disabled={disabled} data-testid={sharedTestIds.detailAction(id)}>
										<Icon />
									</IconButton>
								</span>
							</Tooltip>
						))}
					</Box>
				)}
			</Box>
			<Box sx={{ p: 1.5, display: "flex", flexDirection: "column", gap: 1 }}>{children}</Box>
		</Box>
	);
}

interface DetailSectionProps {
	id: string;
	title: string;
	/** Open at the start; true by default. */
	defaultOpen?: boolean;
	children?: ReactNode;
}

/** A section of the detail panel that folds in and out; it keeps its own open state. */
export function DetailSection({ id, title, defaultOpen = true, children }: DetailSectionProps) {
	const [open, setOpen] = useState(defaultOpen);
	return (
		<Box component="section" data-testid={sharedTestIds.detailSection(id)}>
			<Box
				component="button"
				type="button"
				aria-expanded={open}
				onClick={() => setOpen((current) => !current)}
				data-testid={sharedTestIds.detailSectionToggle(id)}
				sx={{ display: "flex", alignItems: "center", width: "100%", bgcolor: "transparent", border: 0, color: "text.secondary", cursor: "pointer", p: 0, textAlign: "left" }}
			>
				<ExpandMoreIcon fontSize="small" sx={{ transform: open ? "none" : "rotate(-90deg)", transition: "transform .15s" }} />
				<Typography variant="overline">{title}</Typography>
			</Box>
			<Collapse in={open} unmountOnExit>
				<Box sx={{ pt: 0.5, display: "flex", flexDirection: "column", gap: 1 }}>{children}</Box>
			</Collapse>
		</Box>
	);
}

/** A read-only field: a small label and the value below it. */
export function DetailField({ id, label, children }: { id: string; label: string; children: ReactNode }) {
	return (
		<Box data-testid={sharedTestIds.detailField(id)}>
			<Typography variant="caption" color="text.secondary" component="div">
				{label}
			</Typography>
			<Typography variant="body2" component="div">
				{children}
			</Typography>
		</Box>
	);
}
