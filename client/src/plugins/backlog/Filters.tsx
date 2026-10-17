import { useTranslation } from "react-i18next";
import { FilterSection } from "../../shared";
import { PRIORITIES, STATUSES, priorityColor, statusColor } from "./constants";
import { useBacklogState } from "./state";

/** Sidebar section: which statuses are shown. */
export function StatusFilter() {
	const { t } = useTranslation("backlog");
	const { hiddenStatuses, setHiddenStatuses } = useBacklogState();
	return (
		<FilterSection
			title={t("filter.status")}
			options={STATUSES.map((value) => ({ value, label: t(`status.${value}`), color: statusColor(value) }))}
			selected={STATUSES.filter((value) => !hiddenStatuses.includes(value))}
			onChange={(shown) => setHiddenStatuses(STATUSES.filter((value) => !shown.includes(value)))}
		/>
	);
}

/** Sidebar section: which priorities are shown. */
export function PriorityFilter() {
	const { t } = useTranslation("backlog");
	const { hiddenPriorities, setHiddenPriorities } = useBacklogState();
	return (
		<FilterSection
			title={t("filter.priority")}
			options={PRIORITIES.map((value) => ({ value, label: t(`priority.${value}`), color: priorityColor(value) }))}
			selected={PRIORITIES.filter((value) => !hiddenPriorities.includes(value))}
			onChange={(shown) => setHiddenPriorities(PRIORITIES.filter((value) => !shown.includes(value)))}
		/>
	);
}
