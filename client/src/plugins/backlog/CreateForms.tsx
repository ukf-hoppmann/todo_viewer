import { useCreateDialog } from "../workspace";
import { ItemForm } from "./ItemForm";

function CreateForm({ type }: { type: "Epic" | "Story" | "Task" }) {
	const { close, projectUid } = useCreateDialog();
	if (!projectUid) return null;
	return <ItemForm key={projectUid} projectUid={projectUid} type={type} onDone={close} onCancel={close} />;
}

/** The forms the plugin hangs into the "＋ New" dialog of `workspace` (slot `workspace.create-types`). */
export const CreateEpic = () => <CreateForm type="Epic" />;
export const CreateStory = () => <CreateForm type="Story" />;
export const CreateTask = () => <CreateForm type="Task" />;
