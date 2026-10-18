import { IconButton, Tooltip, type IconButtonProps } from "@mui/material";
import type { ComponentType, MouseEvent } from "react";

interface IconActionProps {
	/** Also the accessible name and the tooltip; translated by the caller. */
	label: string;
	icon: ComponentType<{ fontSize?: "small" | "medium" | "inherit" }>;
	onClick: (event: MouseEvent<HTMLButtonElement>) => void;
	disabled?: boolean;
	size?: IconButtonProps["size"];
	color?: IconButtonProps["color"];
	testId?: string;
}

/** An action shown as an icon with its label as tooltip and accessible name (instead of a text button). */
export function IconAction({ label, icon: Icon, onClick, disabled, size = "small", color, testId }: IconActionProps) {
	return (
		<Tooltip title={label}>
			<span>
				<IconButton aria-label={label} size={size} color={color} onClick={onClick} disabled={disabled} data-testid={testId}>
					<Icon fontSize={size === "small" ? "small" : "medium"} />
				</IconButton>
			</span>
		</Tooltip>
	);
}
