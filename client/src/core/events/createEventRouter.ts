import type { ActivePlugin, EventContext } from "../plugins/types";
import type { Logger } from "../logging/types";

/** The topic the core reports itself after the event stream was interrupted and is back. */
export const reconnectedTopic = "core.reconnected";

export interface EventRouter {
	/** The topics at least one active plugin handles (without `core.reconnected`, which the core raises itself). */
	topics(): string[];
	/** Hands an event to the handlers of the active plugins; a failing handler is logged and does not stop the others. */
	handle(topic: string, payload: unknown): void;
}

/** Distributes server events to the plugins that declared a handler for the topic. */
export function createEventRouter(
	active: readonly ActivePlugin[],
	dispatch: EventContext["dispatch"],
	logger: Logger,
): EventRouter {
	return {
		topics() {
			const topics = new Set(active.flatMap(({ definition }) => Object.keys(definition.eventHandlers ?? {})));
			topics.delete(reconnectedTopic);
			return [...topics].sort();
		},

		handle(topic, payload) {
			for (const { id, definition } of active) {
				const handler = definition.eventHandlers?.[topic];
				if (!handler) continue;
				try {
					handler(payload, { dispatch, api: definition.api });
				} catch (error) {
					logger.error({ action: "handle-event", message: `the plugin '${id}' failed to handle '${topic}'`, error });
				}
			}
		},
	};
}
