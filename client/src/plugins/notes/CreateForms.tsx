import { useCreateDialog } from "../workspace";
import { NoteForm } from "./NoteForm";
import { TopicForm } from "./TopicDialogs";

/** The forms the plugin hangs into the "＋ New" dialog of `workspace` (slot `workspace.create-types`). */
export function CreateNote() {
	const { close, projectUid } = useCreateDialog();
	if (!projectUid) return null;
	return <NoteForm key={projectUid} projectUid={projectUid} onDone={close} onCancel={close} />;
}

export function CreateTopic() {
	const { close, projectUid } = useCreateDialog();
	if (!projectUid) return null;
	return <TopicForm key={projectUid} projectUid={projectUid} onDone={close} onCancel={close} />;
}
