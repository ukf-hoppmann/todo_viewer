import { sharedTestIds } from "./testIds";

interface ProgressRingProps {
	done: number;
	total: number;
	/** Diameter in pixels; 18 by default. */
	size?: number;
}

/** Done / total as a pie chart; nothing is drawn for a total of 0. */
export function ProgressRing({ done, total, size = 18 }: ProgressRingProps) {
	if (total <= 0) return null;
	const share = Math.min(Math.max(done / total, 0), 1);
	const radius = size / 2;
	const angle = share * 2 * Math.PI;
	const x = radius + radius * Math.sin(angle);
	const y = radius - radius * Math.cos(angle);
	const large = share > 0.5 ? 1 : 0;
	return (
		<svg
			role="img"
			aria-label={`${done}/${total}`}
			data-testid={sharedTestIds.progressRing}
			width={size}
			height={size}
			viewBox={`0 0 ${size} ${size}`}
			style={{ flexShrink: 0 }}
		>
			<circle cx={radius} cy={radius} r={radius - 1} fill="none" stroke="currentColor" strokeOpacity={0.35} />
			{share >= 1 ? (
				<circle cx={radius} cy={radius} r={radius - 1} fill="currentColor" />
			) : share > 0 ? (
				<path d={`M ${radius} ${radius} L ${radius} 0 A ${radius} ${radius} 0 ${large} 1 ${x} ${y} Z`} fill="currentColor" />
			) : null}
		</svg>
	);
}
