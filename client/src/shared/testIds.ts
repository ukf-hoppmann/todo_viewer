/** Test ids of the shared building blocks (scope client 7); the owner is `shared`. */
export const sharedTestIds = {
	tree: "shared.tree",
	/** A node row: `shared.tree-node.<node id>` (rule 7.2). */
	treeNode: (id: string) => `shared.tree-node.${id}`,
	/** The expand arrow of a node: `shared.tree-toggle.<node id>`. */
	treeToggle: (id: string) => `shared.tree-toggle.${id}`,
	/** The hover actions of a node: `shared.tree-actions.<node id>`. */
	treeActions: (id: string) => `shared.tree-actions.${id}`,
	treeTag: (id: string) => `shared.tree-tag.${id}`,
	treeCount: (id: string) => `shared.tree-count.${id}`,
	/** The drop marker on a node: `shared.tree-drop.<node id>.<position>`. */
	treeDrop: (id: string, position: string) => `shared.tree-drop.${id}.${position}`,
	progressRing: "shared.progress-ring",
	detailPanel: "shared.detail-panel",
	detailTitle: "shared.detail-title",
	/** An action button of the header bar: `shared.detail-action.<id>`. */
	detailAction: (id: string) => `shared.detail-action.${id}`,
	/** A collapsible section: `shared.detail-section.<id>` and its toggle `shared.detail-section-toggle.<id>`. */
	detailSection: (id: string) => `shared.detail-section.${id}`,
	detailSectionToggle: (id: string) => `shared.detail-section-toggle.${id}`,
	detailField: (id: string) => `shared.detail-field.${id}`,
	/** An inline field: `shared.inline-field.<id>` with `…-input` and `…-error`. */
	inlineField: (id: string) => `shared.inline-field.${id}`,
	inlineFieldInput: (id: string) => `shared.inline-field-input.${id}`,
	inlineFieldError: (id: string) => `shared.inline-field-error.${id}`,
	editForm: "shared.edit-form",
	editFormSave: "shared.edit-form-save",
	editFormCancel: "shared.edit-form-cancel",
	editFormError: "shared.edit-form-error",
	editFormConflict: "shared.edit-form-conflict",
	editFormReload: "shared.edit-form-reload",
	markdownView: "shared.markdown-view",
	markdownEditor: "shared.markdown-editor",
	markdownInput: "shared.markdown-input",
	markdownPreview: "shared.markdown-preview",
	markdownSave: "shared.markdown-save",
	markdownConflict: "shared.markdown-conflict",
	markdownShowCurrent: "shared.markdown-show-current",
	markdownSaveAnyway: "shared.markdown-save-anyway",
	filterSection: "shared.filter-section",
	/** A checkbox of a filter section: `shared.filter-option.<value>`. */
	filterOption: (value: string) => `shared.filter-option.${value}`,
	confirmDialog: "shared.confirm-dialog",
	confirmDialogConfirm: "shared.confirm-dialog-confirm",
	confirmDialogCancel: "shared.confirm-dialog-cancel",
	choiceDialog: "shared.choice-dialog",
	/** A choice of the dialog: `shared.choice-dialog-option.<value>`. */
	choiceDialogOption: (value: string) => `shared.choice-dialog-option.${value}`,
	choiceDialogCancel: "shared.choice-dialog-cancel",
	entityPicker: "shared.entity-picker",
	documents: "shared.documents",
	/** A document of the section: `shared.document.<file name>`. */
	document: (name: string) => `shared.document.${name}`,
	documentsAddEntry: "shared.documents-add-entry",
	documentsAddSpec: "shared.documents-add-spec",
	documentDialog: "shared.document-dialog",
	documentLarge: "shared.document-large",
	documentEdit: "shared.document-edit",
	documentClose: "shared.document-close",
	documentCancel: "shared.document-cancel",
	documentError: "shared.document-error",
	entryDialog: "shared.entry-dialog",
	/** A field of the entry dialog: `shared.entry-field.<topic|discussed|decided|open|summary>`. */
	entryField: (name: string) => `shared.entry-field.${name}`,
	entrySave: "shared.entry-save",
	specName: "shared.spec-name",
	specSave: "shared.spec-save",
	largeView: "shared.large-view",
	largeViewClose: "shared.large-view-close",
	largeViewToc: "shared.large-view-toc",
	/** An entry of the table of contents: `shared.large-view-toc-item.<slug>`. */
	largeViewTocItem: (slug: string) => `shared.large-view-toc-item.${slug}`,
} as const;
