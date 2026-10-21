import { List, ListItemButton, ListItemText } from "@mui/material";
import type { SxProps, Theme } from "@mui/material";
import type { Heading } from "./renderMarkdown";

interface OutlineListProps {
	headings: Heading[];
	/** Accessible name of the list. */
	label: string;
	onJump: (slug: string) => void;
	testId: string;
	itemTestId: (slug: string) => string;
	sx?: SxProps<Theme>;
}

/** The headings of a document as a list, indented by depth; a click reports the slug of the heading. */
export function OutlineList({ headings, label, onJump, testId, itemTestId, sx }: OutlineListProps) {
	return (
		<List component="nav" aria-label={label} dense data-testid={testId} sx={sx}>
			{headings.map((heading) => (
				<ListItemButton key={heading.slug} data-testid={itemTestId(heading.slug)} sx={{ pl: 1 + (heading.depth - 1) * 2 }} onClick={() => onJump(heading.slug)}>
					<ListItemText primary={heading.text} slotProps={{ primary: { noWrap: true } }} />
				</ListItemButton>
			))}
		</List>
	);
}
