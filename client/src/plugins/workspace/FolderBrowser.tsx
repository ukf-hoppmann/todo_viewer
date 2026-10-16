import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import FolderIcon from "@mui/icons-material/Folder";
import { Button, Dialog, DialogActions, DialogContent, DialogTitle, IconButton, List, ListItemButton, ListItemIcon, ListItemText, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useBrowseFoldersQuery } from "./api";
import { workspaceTestIds } from "./testIds";

interface Props {
	/** Where to start; the server's start folder if empty. */
	start?: string;
	onChoose: (path: string) => void;
	onCancel: () => void;
}

/** Browses the folders of the server's machine and returns the chosen one (the mirror folder of a project). */
export function FolderBrowser({ start, onChoose, onCancel }: Props) {
	const { t } = useTranslation("workspace");
	const [path, setPath] = useState<string | undefined>(start || undefined);
	const { data, isFetching } = useBrowseFoldersQuery(path);

	return (
		<Dialog open onClose={onCancel} fullWidth maxWidth="sm" slotProps={{ paper: { "data-testid": workspaceTestIds.folderBrowser } as never }}>
			<DialogTitle sx={{ display: "flex", alignItems: "center", gap: 1 }}>
				<IconButton
					size="small"
					aria-label={t("folders.up")}
					disabled={!data?.parent}
					onClick={() => data?.parent && setPath(data.parent)}
					data-testid={workspaceTestIds.folderUp}
				>
					<ArrowUpwardIcon fontSize="small" />
				</IconButton>
				<Typography component="span" variant="body2" sx={{ wordBreak: "break-all" }}>
					{data?.path ?? t("folders.loading")}
				</Typography>
			</DialogTitle>
			<DialogContent dividers sx={{ minHeight: 240 }}>
				{data?.error && <Typography color="error">{data.error}</Typography>}
				<List dense disablePadding aria-busy={isFetching}>
					{(data?.folders ?? []).map((folder) => (
						<ListItemButton
							key={folder.name}
							onClick={() => setPath(`${data?.path ?? ""}/${folder.name}`)}
							data-testid={workspaceTestIds.folder(folder.name)}
						>
							<ListItemIcon sx={{ minWidth: 32 }}>
								<FolderIcon fontSize="small" color={folder.has_mirror ? "primary" : "inherit"} />
							</ListItemIcon>
							<ListItemText primary={folder.name} secondary={folder.has_mirror ? t("folders.hasMirror") : undefined} />
						</ListItemButton>
					))}
					{data && !data.error && (data.folders ?? []).length === 0 && <Typography variant="body2">{t("folders.empty")}</Typography>}
				</List>
			</DialogContent>
			<DialogActions>
				<Button onClick={onCancel}>{t("card.cancel")}</Button>
				<Button variant="contained" disabled={!data} onClick={() => data && onChoose(data.path)} data-testid={workspaceTestIds.folderChoose}>
					{t("folders.choose")}
				</Button>
			</DialogActions>
		</Dialog>
	);
}
