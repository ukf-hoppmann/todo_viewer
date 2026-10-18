// Public API of `shared` (scope client 1): generated API types and the building blocks of the plugins.
// Nothing here holds global store state; texts come in through properties.
export type { components, operations, paths } from "./api/schema";
export { ConfirmDialog, ChoiceDialog, type Choice } from "./dialogs/Dialogs";
export { DetailField, DetailPanel, DetailSection, type DetailAction } from "./DetailPanel";
export { DocumentsSection, type DocumentsLabels, type DocumentsSectionProps, type NotesEntry, type StoredDocument } from "./documents/DocumentsSection";
export { EditForm, type EditFormLabels } from "./EditForm";
export { EntityPicker } from "./EntityPicker";
export { entityText, type Entity } from "./entityText";
export { FilterSection, type FilterOption } from "./FilterSection";
export { IconAction } from "./IconAction";
export { InlineField, type FieldOption, type InlineFieldProps } from "./InlineField";
export { LargeView } from "./markdown/LargeView";
export { MarkdownEditor, type MarkdownEditorLabels } from "./markdown/MarkdownEditor";
export { MarkdownView } from "./markdown/MarkdownView";
export { extractHeadings, renderMarkdown, slugify, type Heading } from "./markdown/renderMarkdown";
export { ProgressRing } from "./ProgressRing";
export { sharedTestIds } from "./testIds";
export { TreeView, type TreeDrop } from "./tree/TreeView";
export { ancestorsOf, buildTree, dropPosition, flattenVisible, guideLines, isInSubtree } from "./tree/treeModel";
export type { DropPosition, FlatNode, TreeNode, VisibleNode } from "./tree/treeModel";
