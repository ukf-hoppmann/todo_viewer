import { Button, Dialog, DialogActions, DialogContent, DialogTitle, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { ChoiceDialog } from "../../shared";
import type { ItemOut, RetypeOut } from "./api";

/** The outcome shown after a type change: the result, or the message of the failure. */
export type RetypeResult = RetypeOut | { error: string };
import { ItemForm } from "./ItemForm";
import { TYPES } from "./constants";
import { backlogTestIds } from "./testIds";
import { useItemWrite } from "./useItemWrite";

/** The form in a dialog: edit an item, or create one (below `parentUid` if given). Reset when the item's version changes. */
export function ItemFormDialog({
	projectUid,
	type,
	item,
	parentUid,
	onClose,
}: {
	projectUid: string;
	type: string;
	item?: ItemOut;
	parentUid?: string | null;
	onClose: () => void;
}) {
	const { t } = useTranslation("backlog");
	return (
		<Dialog open onClose={onClose} fullWidth maxWidth="md" slotProps={{ paper: { "data-testid": backlogTestIds.formDialog } as never }}>
			<DialogTitle>{item ? t("form.editTitle", { label: item.label }) : t("form.createTitle", { type: t(`type.${type}`) })}</DialogTitle>
			<DialogContent dividers>
				<ItemForm key={item?.version ?? "new"} projectUid={projectUid} type={type} item={item} parentUid={parentUid} onDone={onClose} onCancel={onClose} />
			</DialogContent>
		</Dialog>
	);
}

/** Choose the new type of an item; afterwards the notice names the old and the new label. */
export function RetypeDialog({ item, onClose, onDone }: { item: ItemOut; onClose: () => void; onDone: (result: RetypeResult) => void }) {
	const { t } = useTranslation("backlog");
	const write = useItemWrite();
	return (
		<>
			<ChoiceDialog
				open
				title={t("retype.title", { label: item.label })}
				message={t("retype.message")}
				cancelLabel={t("form.cancel")}
				choices={TYPES.filter((type) => type !== item.type).map((type) => ({ value: type, label: t(`type.${type}`) }))}
				onCancel={onClose}
				onChoose={(type) => {
					void write.retypeItem(item, type).then(onDone, (failure: Error) => onDone({ error: failure.message }));
				}}
			/>
			{write.dialog}
		</>
	);
}

/** What changed after a type change, with the hint about references outside the backlog. */
export function RetypeNotice({ result, onClose }: { result: RetypeResult; onClose: () => void }) {
	const { t } = useTranslation("backlog");
	return (
		<Dialog open onClose={onClose} slotProps={{ paper: { "data-testid": backlogTestIds.retypeNotice } as never }}>
			<DialogTitle>{"error" in result ? t("retype.failed") : t("retype.done", { old: result.old_label, new: result.new_label })}</DialogTitle>
			<DialogContent>
				{"error" in result ? (
					<Typography color="error">{result.error}</Typography>
				) : (
					result.notices.map((notice) => (
						<Typography key={notice.code} variant="body2">
							{t(`retype.notice.${notice.code}`, { old: notice.details.old_label, new: notice.details.new_label, defaultValue: notice.message })}
						</Typography>
					))
				)}
			</DialogContent>
			<DialogActions>
				<Button onClick={onClose}>{t("form.close")}</Button>
			</DialogActions>
		</Dialog>
	);
}
