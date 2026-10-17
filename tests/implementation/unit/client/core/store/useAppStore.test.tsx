import { createSlice } from "@reduxjs/toolkit";
import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { createAppStore } from "../../../../../../client/src/core/store/createAppStore";
import { StoreProvider } from "../../../../../../client/src/core/store/StoreProvider";
import { useAppDispatch, useAppSelector } from "../../../../../../client/src/core/store/hooks";
import type { PluginRegistry } from "../../../../../../client/src/core/plugins/types";
import { fakeConnection } from "../../../../../helpers/client/fakeBackend";

const { connection } = fakeConnection();

const slice = createSlice({ name: "x", initialState: { value: 3 }, reducers: { up: (state) => void (state.value += 1) } });
const i18n = { de: {}, en: {}, fr: {} };

/** A registry with one active plugin `a` that owns the slice. */
const registry: PluginRegistry = {
	active: () => [{ id: "a", definition: { i18n, reducer: slice.reducer } }],
	statuses: () => [],
};

function Counter() {
	const value = useAppSelector((state) => (state.a as { value: number }).value);
	const dispatch = useAppDispatch();
	return <button onClick={() => dispatch(slice.actions.up())}>{value}</button>;
}

describe("the store in React", () => {
	afterEach(cleanup);

	it("lets a component read its compartment and change it with an action", () => {
		render(
			<StoreProvider store={createAppStore({ registry, connection })}>
				<Counter />
			</StoreProvider>,
		);
		expect(screen.getByRole("button").textContent).toBe("3");

		act(() => screen.getByRole("button").click());

		expect(screen.getByRole("button").textContent).toBe("4");
	});
});
