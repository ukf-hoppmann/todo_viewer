import { useTranslation } from "react-i18next";
import { FilterSection } from "../../shared";
import { STATUSES, statusColor } from "./constants";
import { useMemosState } from "./state";

/** The option of the status section that shows archived topics with their content (no status of its own). */
export const ARCHIVED_TOPICS = "archived-topics";

/** Sidebar section: which memo statuses are shown (the open ones by default), and whether archived topics are. */
export function StatusFilter() {
	const { t } = useTranslation("memos");
	const { shownStatuses, setShownStatuses, showArchivedTopics, setShowArchivedTopics } = useMemosState();
	return (
		<FilterSection
			title={t("filter.status")}
			options={[...STATUSES.map((value) => ({ value, label: t(`status.${value}`), color: statusColor(value) })), { value: ARCHIVED_TOPICS, label: t("archivedTopics") }]}
			selected={showArchivedTopics ? [...shownStatuses, ARCHIVED_TOPICS] : shownStatuses}
			onChange={(shown) => {
				setShownStatuses(STATUSES.filter((value) => shown.includes(value)));
				if (shown.includes(ARCHIVED_TOPICS) !== showArchivedTopics) setShowArchivedTopics(!showArchivedTopics);
			}}
		/>
	);
}
