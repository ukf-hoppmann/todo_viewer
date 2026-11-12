import { useShownElement } from "../workspace";
import { MemoDetail } from "./MemoDetail";

/** The detail of a memo wherever another plugin shows an element (`workspace.element-detail`). */
export default function MemoElementView() {
	const { uid, onClose } = useShownElement();
	return <MemoDetail uid={uid} onClose={onClose} />;
}
