import { Box, Checkbox, FormControlLabel, FormGroup, Typography } from "@mui/material";
import { sharedTestIds } from "./testIds";

export interface FilterOption {
	value: string;
	label: string;
	/** A color for the dot before the label (any CSS color). */
	color?: string;
	/** A number after the label, e.g. how many elements match. */
	count?: number;
}

interface FilterSectionProps {
	title: string;
	options: readonly FilterOption[];
	selected: readonly string[];
	onChange: (selected: string[]) => void;
}

/** A group of check boxes with a colored dot each, for the sidebar. The caller keeps the selection. */
export function FilterSection({ title, options, selected, onChange }: FilterSectionProps) {
	const toggle = (value: string) => onChange(selected.includes(value) ? selected.filter((entry) => entry !== value) : [...selected, value]);
	return (
		<Box data-testid={sharedTestIds.filterSection} component="section" aria-label={title}>
			<Typography variant="overline" color="text.secondary" component="h3">
				{title}
			</Typography>
			<FormGroup>
				{options.map((option) => (
					<FormControlLabel
						key={option.value}
						control={
							<Checkbox
								size="small"
								checked={selected.includes(option.value)}
								onChange={() => toggle(option.value)}
								slotProps={{ input: { "data-testid": sharedTestIds.filterOption(option.value) } as never }}
							/>
						}
						label={
							<Box sx={{ display: "flex", alignItems: "center", gap: 0.75 }}>
								{option.color && <Box sx={{ width: 10, height: 10, borderRadius: "50%", bgcolor: option.color }} />}
								<Typography variant="body2">{option.label}</Typography>
								{option.count !== undefined && (
									<Typography variant="caption" color="text.secondary">
										{option.count}
									</Typography>
								)}
							</Box>
						}
					/>
				))}
			</FormGroup>
		</Box>
	);
}
