import { useShownElement } from "../workspace";
import { ItemDetail } from "./ItemDetail";

const nothing = () => undefined;

/** The detail of an epic, story or task wherever another plugin shows an element (`workspace.element-detail`). */
export default function ItemElementView() {
	const { uid, onClose, onSelect } = useShownElement();
	return <ItemDetail uid={uid} onSelect={onSelect ?? nothing} onClose={onClose} />;
}
