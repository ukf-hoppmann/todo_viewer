import type { Logger } from "../logging/types";
import type { ActivePlugin, EventContext } from "../plugins/types";
import { createEventRouter, reconnectedTopic } from "./createEventRouter";
import { createEventStream, type EventStream, type EventStreamOptions } from "./createEventStream";

export interface StartEventsOptions {
	active: readonly ActivePlugin[];
	dispatch: EventContext["dispatch"];
	logger: Logger;
	/** The address of the stream; `/api/core/events` by default. */
	url?: string;
	/** For tests: a fake `EventSource`, timers and wait times. */
	stream?: Pick<EventStreamOptions, "createSource" | "schedule" | "backoff">;
}

/** Opens the event stream and routes its events to the active plugins; `stop()` closes it. */
export function startEvents({ active, dispatch, logger, url = "/api/core/events", stream }: StartEventsOptions): EventStream {
	const router = createEventRouter(active, dispatch, logger);
	const events = createEventStream({
		url,
		topics: router.topics,
		onEvent: router.handle,
		onReconnected: () => router.handle(reconnectedTopic, {}),
		onProblem: (message, error) => logger.warn({ action: "event-stream", message, error }),
		...stream,
	});
	events.start();
	return events;
}
