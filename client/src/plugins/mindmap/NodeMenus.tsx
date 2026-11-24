import { Menu, MenuItem } from "@mui/material";
import { useTranslation } from "react-i18next";
import { ConfirmDialog } from "../../shared";
import { errorMessage, useDeleteNodeMutation, useListNodeTreesQuery, type NodeTreeOut } from "./api";
import { mindmapTestIds } from "./testIds";

export type MenuAnchor = HTMLElement | { top: number; left: number };

function anchorProps(anchor: MenuAnchor) {
	return anchor instanceof HTMLElement
		? { anchorEl: anchor, anchorReference: "anchorEl" as const }
		: { anchorReference: "anchorPosition" as const, anchorPosition: anchor };
}

/**
 * The menu of a node (right click or the button of its actions): hang it over to or transfer it to another map, transfer its branch into the backlog ("Ast überführen") and,
 * depending on where it stands, remove or delete it. A node in one tree only is deleted ("Löschen"); one in several is
 * either taken out of this tree without a question ("Hier entfernen") or deleted everywhere ("Knoten löschen", after a question).
 */
export function NodeMenu({ anchor, shared, onClose, onMove, onTransfer, onTransferBranch, onRemoveHere, onDelete }: {
	anchor: MenuAnchor;
	shared: boolean;
	onClose: () => void;
	onMove: () => void;
	onTransfer: () => void;
	onTransferBranch: () => void;
	onRemoveHere: () => void;
	onDelete: () => void;
}) {
	const { t } = useTranslation("mindmap");
	const pick = (action: () => void) => () => {
		onClose();
		action();
	};
	return (
		<Menu open onClose={onClose} {...anchorProps(anchor)} data-testid={mindmapTestIds.nodeMenu}>
			<MenuItem onClick={pick(onMove)} data-testid={mindmapTestIds.nodeMenuMove}>
				{t("menu.move")}
			</MenuItem>
			<MenuItem onClick={pick(onTransfer)} data-testid={mindmapTestIds.nodeMenuTransfer}>
				{t("menu.transfer")}
			</MenuItem>
			<MenuItem onClick={pick(onTransferBranch)} data-testid={mindmapTestIds.nodeMenuTransferBranch}>
				{t("menu.transferBranch")}
			</MenuItem>
			{shared && (
				<MenuItem onClick={pick(onRemoveHere)} data-testid={mindmapTestIds.nodeMenuRemoveHere}>
					{t("menu.removeHere")}
				</MenuItem>
			)}
			<MenuItem onClick={pick(onDelete)} data-testid={mindmapTestIds.nodeMenuDelete}>
				{t(shared ? "menu.deleteNode" : "menu.delete")}
			</MenuItem>
		</Menu>
	);
}

/** The trees a node stands in, one entry each; choosing one goes there. */
export function TreeJumpMenu({ anchor, node, onClose, onPick }: { anchor: MenuAnchor; node: string; onClose: () => void; onPick: (tree: NodeTreeOut) => void }) {
	const { t } = useTranslation("mindmap");
	const { data: trees } = useListNodeTreesQuery(node);
	return (
		<Menu open onClose={onClose} {...anchorProps(anchor)} data-testid={mindmapTestIds.treeJumpMenu}>
			{(trees ?? []).map((tree) => (
				<MenuItem key={tree.tree_uid} onClick={() => onPick(tree)} data-testid={mindmapTestIds.treeJump(tree.tree_uid)}>
					{tree.kind === "project" ? t("maps.projectTree", { name: tree.name }) : tree.name}
				</MenuItem>
			))}
		</Menu>
	);
}

/** The question before "Knoten löschen" of a node that stands in several trees: it names the trees it leaves. */
export function DeleteSharedDialog({ node, title, version, onClose, onFail }: { node: string; title: string; version: number; onClose: () => void; onFail: (message: string) => void }) {
	const { t } = useTranslation("mindmap");
	const { data: trees } = useListNodeTreesQuery(node);
	const [deleteNode] = useDeleteNodeMutation();
	return (
		<ConfirmDialog
			open
			title={t("sharedDelete.title", { title })}
			message={t("sharedDelete.message", { trees: (trees ?? []).map((tree) => (tree.kind === "project" ? t("maps.projectTree", { name: tree.name }) : tree.name)).join(", ") })}
			confirmLabel={t("sharedDelete.confirm")}
			cancelLabel={t("form.cancel")}
			onCancel={onClose}
			onConfirm={() => {
				onClose();
				void deleteNode({ ref: node, version }).unwrap().catch((failure: unknown) => onFail(errorMessage(failure, t("error.failed"))));
			}}
		/>
	);
}
