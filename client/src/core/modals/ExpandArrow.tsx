/** Small arrow that turns upside down when its section is open. */
export function ExpandArrow({ open }: { open: boolean }) {
	return (
		<svg
			width="16"
			height="16"
			viewBox="0 0 16 16"
			aria-hidden="true"
			focusable="false"
			style={{ transform: open ? "rotate(180deg)" : undefined, transition: "transform 150ms" }}
		>
			<path d="M3 6l5 5 5-5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
		</svg>
	);
}
