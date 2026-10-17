import { useCreateDialog } from "../workspace";
import { AlarmForm } from "./AlarmForm";

/** The form the plugin hangs into the "＋ New" dialog of `workspace` (slot `workspace.create-types`). */
export function CreateAlarm() {
	const { close, projectUid } = useCreateDialog();
	if (!projectUid) return null;
	return <AlarmForm key={projectUid} projectUid={projectUid} onDone={close} onCancel={close} />;
}
