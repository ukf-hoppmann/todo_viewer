import { cleanup, render } from "@testing-library/react";
import { useEffect } from "react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { LoggerOriginProvider } from "../../../../../../client/src/core/logging/LoggerOriginProvider";
import { logging } from "../../../../../../client/src/core/logging/logging";
import { MemorySink } from "../../../../../../client/src/core/logging/MemorySink";
import type { Logger } from "../../../../../../client/src/core/logging/types";
import { useLogger } from "../../../../../../client/src/core/logging/useLogger";

function Probe({ message }: { message: string }) {
	useLogger().info(message);
	return null;
}

describe("useLogger", () => {
	const sink = new MemorySink("useLogger-test");

	beforeEach(() => {
		logging.addSink(sink, { level: "debug" });
	});

	afterEach(() => {
		cleanup();
		logging.removeSink(sink.name);
		sink.clear();
	});

	it("returns the logger of origin core without a provider", () => {
		render(<Probe message="a" />);

		expect(sink.entries[0]).toMatchObject({ origin: "core", message: "a" });
	});

	it("returns the logger of the nearest LoggerOriginProvider", () => {
		render(
			<LoggerOriginProvider origin="variant-filter">
				<Probe message="outer" />
				<LoggerOriginProvider origin="process-manager">
					<Probe message="inner" />
				</LoggerOriginProvider>
			</LoggerOriginProvider>,
		);

		expect(sink.entries.map((entry) => [entry.origin, entry.message])).toEqual([
			["variant-filter", "outer"],
			["process-manager", "inner"],
		]);
	});

	it("returns the same logger as logging.forOrigin", () => {
		let captured: Logger | undefined;
		function Capture({ onLogger }: { onLogger: (logger: Logger) => void }) {
			const logger = useLogger();
			useEffect(() => {
				onLogger(logger);
			}, [logger, onLogger]);
			return null;
		}

		render(
			<LoggerOriginProvider origin="variant-filter">
				<Capture
					onLogger={(logger) => {
						captured = logger;
					}}
				/>
			</LoggerOriginProvider>,
		);

		expect(captured).toBe(logging.forOrigin("variant-filter"));
	});

	it("rejects an invalid origin", () => {
		const error = console.error;
		console.error = () => {};
		try {
			expect(() =>
				render(
					<LoggerOriginProvider origin="Bad Origin">
						<Probe message="x" />
					</LoggerOriginProvider>,
				),
			).toThrow();
		} finally {
			console.error = error;
		}
	});
});
