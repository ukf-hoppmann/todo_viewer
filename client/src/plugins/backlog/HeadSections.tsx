import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { HEAD_KEYS, parseHead } from "./model";
import { backlogTestIds as ids } from "./testIds";

const DATE_AT_END = /^(.*?)\s*\((\d{4}-\d{2}-\d{2})\)$/;
const EMPTY = /^(keine?|nichts|none|-)\.?$/i;

/** A bullet; a date in brackets at its end is set apart in a dimmer color. */
function Bullet({ text, small }: { text: string; small: boolean }) {
	const match = DATE_AT_END.exec(text);
	return (
		<Box component="li" sx={{ display: "flex", gap: 0.75, alignItems: "baseline" }}>
			<Box component="span" aria-hidden sx={{ color: "text.disabled" }}>
				•
			</Box>
			<Typography variant={small ? "caption" : "body2"} component="span" sx={{ minWidth: 0, overflowWrap: "anywhere" }}>
				{match ? match[1] : text}
				{match && (
					<Typography variant="caption" component="span" color="text.secondary" sx={{ ml: 0.75, whiteSpace: "nowrap" }}>
						{match[2]}
					</Typography>
				)}
			</Typography>
		</Box>
	);
}

/**
 * The head of the notes as a short overview: every key (Goal/Status, Next step, Open, Decided, References) in
 * an accent color and translated, its text below it, the bullets as a list. Text that is not in this form is shown
 * as it is. `compact` is the smaller variant for the tooltip in the list.
 */
export function HeadSections({ content, compact = false }: { content: string; compact?: boolean }) {
	const { t } = useTranslation("backlog");
	const sections = parseHead(content);
	if (sections.length === 0) {
		return (
			<Typography variant={compact ? "caption" : "body2"} component="div" sx={{ whiteSpace: "pre-wrap" }}>
				{content}
			</Typography>
		);
	}
	return (
		<Box sx={{ display: "flex", flexDirection: "column", gap: compact ? 0.75 : 1 }}>
			{sections.map((section, index) => {
				const id = HEAD_KEYS[section.key];
				const nothing = section.items.length === 0 && EMPTY.test(section.text);
				return (
					<Box key={`${section.key}.${index}`} data-testid={ids.notesHeadSection(section.key)}>
						<Typography variant="caption" component="div" sx={{ color: "primary.main", fontWeight: "bold", letterSpacing: 0.3, textTransform: "uppercase" }}>
							{id ? t(`notes.key.${id}`) : section.key}
						</Typography>
						{section.text && (
							<Typography variant={compact ? "caption" : "body2"} component="div" color={nothing ? "text.secondary" : undefined} sx={{ overflowWrap: "anywhere" }}>
								{section.text}
							</Typography>
						)}
						{section.items.length > 0 && (
							<Box component="ul" sx={{ listStyle: "none", m: 0, p: 0, mt: section.text ? 0.25 : 0, display: "flex", flexDirection: "column", gap: 0.25 }}>
								{section.items.map((item, position) => (
									<Bullet key={position} text={item} small={compact} />
								))}
							</Box>
						)}
					</Box>
				);
			})}
		</Box>
	);
}
