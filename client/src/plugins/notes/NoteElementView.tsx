import { useShownElement } from "../workspace";
import { NoteDetail } from "./NoteDetail";

/** The detail of a note wherever another plugin shows an element (`workspace.element-detail`). */
export default function NoteElementView() {
	const { uid, onClose } = useShownElement();
	return <NoteDetail uid={uid} onClose={onClose} />;
}
