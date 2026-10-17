import { useTranslation } from "react-i18next";
import { FilterSection } from "../../shared";
import { STATUSES, statusColor } from "./constants";
import { useNotesState } from "./state";

/** Sidebar section: which note statuses are shown (the open ones by default). */
export function StatusFilter() {
	const { t } = useTranslation("notes");
	const { shownStatuses, setShownStatuses } = useNotesState();
	return (
		<FilterSection
			title={t("filter.status")}
			options={STATUSES.map((value) => ({ value, label: t(`status.${value}`), color: statusColor(value) }))}
			selected={shownStatuses}
			onChange={(shown) => setShownStatuses(STATUSES.filter((value) => shown.includes(value)))}
		/>
	);
}
