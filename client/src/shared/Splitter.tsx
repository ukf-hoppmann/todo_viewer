import RestartAltIcon from "@mui/icons-material/RestartAlt";
import { Box } from "@mui/material";
import { useRef, type KeyboardEvent, type PointerEvent } from "react";
import { IconAction } from "./IconAction";
import { sharedTestIds } from "./testIds";

const KEY_STEP = 24;

export interface SplitterProps {
	/** Names the bar in test ids (`shared.splitter.<id>`). */
	id: string;
	/** Accessible name of the bar and of its reset button; translated by the caller. */
	label: string;
	resetLabel: string;
	/** The width of the panel the bar resizes, in px. */
	width: number;
	min: number;
	max: number;
	/** Where the panel lies: dragging towards it narrows it. */
	panel: "before" | "after";
	/** During a drag, with the width the panel would have; the caller shows it without saving. */
	onLive: (width: number) => void;
	/** At the end of a drag or a key press: the width to keep. */
	onCommit: (width: number) => void;
	/** The reset icon is shown only while the width differs from the basic setting. */
	canReset: boolean;
	onReset: () => void;
}

/** A draggable bar between two areas that resizes one of them, with an icon that brings back the basic setting. */
export function Splitter({ id, label, resetLabel, width, min, max, panel, onLive, onCommit, canReset, onReset }: SplitterProps) {
	const drag = useRef<{ x: number; width: number; last: number }>(undefined);
	const clamp = (value: number) => Math.round(Math.min(max, Math.max(min, value)));
	const widthAt = (start: { x: number; width: number }, x: number) => clamp(start.width + (panel === "after" ? start.x - x : x - start.x));

	const down = (event: PointerEvent<HTMLElement>) => {
		if (event.button !== 0) return;
		event.currentTarget.setPointerCapture(event.pointerId);
		drag.current = { x: event.clientX, width, last: width };
	};
	const move = (event: PointerEvent<HTMLElement>) => {
		const start = drag.current;
		if (!start) return;
		start.last = widthAt(start, event.clientX);
		onLive(start.last);
	};
	const up = () => {
		const start = drag.current;
		drag.current = undefined;
		if (start && start.last !== start.width) onCommit(start.last);
	};
	const key = (event: KeyboardEvent<HTMLElement>) => {
		const sign = event.key === "ArrowLeft" ? -1 : event.key === "ArrowRight" ? 1 : 0;
		if (sign === 0) return;
		event.preventDefault();
		onCommit(clamp(width + (panel === "after" ? -sign : sign) * KEY_STEP));
	};

	return (
		<Box
			role="separator"
			aria-orientation="vertical"
			aria-label={label}
			aria-valuenow={width}
			aria-valuemin={min}
			aria-valuemax={max}
			tabIndex={0}
			data-testid={sharedTestIds.splitter(id)}
			onPointerDown={down}
			onPointerMove={move}
			onPointerUp={up}
			onPointerCancel={up}
			onKeyDown={key}
			sx={{
				position: "relative",
				flexShrink: 0,
				width: 8,
				cursor: "col-resize",
				touchAction: "none",
				"&:hover, &:focus-visible": { bgcolor: "action.hover" },
			}}
		>
			{canReset && (
				<Box sx={{ position: "absolute", top: 4, left: "50%", transform: "translateX(-50%)", zIndex: 1, bgcolor: "background.paper", borderRadius: "50%" }} onPointerDown={(event) => event.stopPropagation()}>
					<IconAction label={resetLabel} icon={RestartAltIcon} onClick={onReset} testId={sharedTestIds.splitterReset(id)} />
				</Box>
			)}
		</Box>
	);
}
