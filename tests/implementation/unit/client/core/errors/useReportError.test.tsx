import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useEffect } from "react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
	errors,
	LoggerOriginProvider,
	logging,
	MemorySink,
	modals,
	useReportError,
	type ReportError,
} from "../../../../../../client/src/core";

function Reporter({ text }: { text: string }) {
	const reportError = useReportError();
	return <button data-testid={`test.report-${text}`} onClick={() => void reportError({ userMessage: text })} />;
}

describe("useReportError", () => {
	const sink = new MemorySink("useReportError-test");

	beforeEach(() => {
		logging.addSink(sink, { level: "debug" });
	});

	afterEach(() => {
		cleanup();
		logging.removeSink(sink.name);
		sink.clear();
		for (let pending = modals.getSnapshot(); pending; pending = modals.getSnapshot()) {
			if (pending.kind === "alert") pending.close();
			else break;
		}
	});

	it("reports with the origin core without a provider", () => {
		render(<Reporter text="a" />);

		fireEvent.click(screen.getByTestId("test.report-a"));

		expect(sink.entries).toHaveLength(1);
		expect(sink.entries[0]).toMatchObject({ origin: "core", level: "error", userMessage: "a" });
		expect(modals.getSnapshot()?.kind).toBe("alert");
	});

	it("reports with the origin of the nearest LoggerOriginProvider", () => {
		render(
			<LoggerOriginProvider origin="variant-filter">
				<Reporter text="outer" />
				<LoggerOriginProvider origin="process-manager">
					<Reporter text="inner" />
				</LoggerOriginProvider>
			</LoggerOriginProvider>,
		);

		fireEvent.click(screen.getByTestId("test.report-outer"));
		fireEvent.click(screen.getByTestId("test.report-inner"));

		expect(sink.entries.map((entry) => [entry.origin, entry.userMessage])).toEqual([
			["variant-filter", "outer"],
			["process-manager", "inner"],
		]);
	});

	it("returns the function of errors.forOrigin", () => {
		let reporter: ReportError | undefined;
		function Capture({ onReporter }: { onReporter: (value: ReportError) => void }) {
			const value = useReportError();
			useEffect(() => {
				onReporter(value);
			}, [value, onReporter]);
			return null;
		}

		render(
			<LoggerOriginProvider origin="variant-filter">
				<Capture
					onReporter={(value) => {
						reporter = value;
					}}
				/>
			</LoggerOriginProvider>,
		);

		expect(reporter).toBe(errors.forOrigin("variant-filter"));
	});
});
