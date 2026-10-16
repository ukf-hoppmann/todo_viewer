import CheckIcon from "@mui/icons-material/Check";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import LightModeIcon from "@mui/icons-material/LightMode";
import SettingsBrightnessIcon from "@mui/icons-material/SettingsBrightness";
import { IconButton, ListItemIcon, ListItemText, Menu, MenuItem, Tooltip, useColorScheme } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { coreTestIds } from "../testIds";

type ColorMode = "light" | "dark" | "system";

const colorModes: readonly ColorMode[] = ["light", "dark", "system"];

const icons = { light: LightModeIcon, dark: DarkModeIcon, system: SettingsBrightnessIcon } as const;

/**
 * The color scheme as a button with a menu in the app bar: light, dark, or the system setting. The button
 * shows the symbol of the choice in effect; the choice with the check mark is the one in effect. MUI keeps the
 * choice itself (in the browser, so it survives a reload) and follows the system setting live as long as the
 * choice is `system`, which is the start value. Needs the `ThemeProvider` of the application above it.
 */
export function ColorSchemeMenu() {
	const { t } = useTranslation("core");
	const { mode, setMode } = useColorScheme();
	const [anchor, setAnchor] = useState<HTMLElement | null>(null);
	const current: ColorMode = mode ?? "system";
	const CurrentIcon = icons[current];
	const label = t("appBar.colorScheme.label");

	const choose = (next: ColorMode) => {
		setMode(next);
		setAnchor(null);
	};

	return (
		<>
			<Tooltip title={label}>
				<IconButton
					color="inherit"
					aria-label={label}
					aria-haspopup="menu"
					aria-expanded={anchor !== null}
					onClick={(event) => setAnchor(event.currentTarget)}
					data-testid={coreTestIds.colorSchemeButton}
				>
					<CurrentIcon data-testid={coreTestIds.colorSchemeIcon(current)} />
				</IconButton>
			</Tooltip>
			<Menu anchorEl={anchor} open={anchor !== null} onClose={() => setAnchor(null)}>
				{colorModes.map((colorMode) => {
					const Icon = icons[colorMode];
					const active = colorMode === current;
					return (
						<MenuItem
							key={colorMode}
							role="menuitemradio"
							aria-checked={active}
							selected={active}
							onClick={() => choose(colorMode)}
							data-testid={coreTestIds.colorSchemeOption(colorMode)}
						>
							<ListItemIcon>
								<Icon fontSize="small" />
							</ListItemIcon>
							<ListItemText>{t(`appBar.colorScheme.${colorMode}`)}</ListItemText>
							{active && <CheckIcon fontSize="small" sx={{ ml: 2 }} />}
						</MenuItem>
					);
				})}
			</Menu>
		</>
	);
}
