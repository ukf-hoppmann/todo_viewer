import { createSlice } from "@reduxjs/toolkit";
import type { AppState } from "../../../core";

interface ExampleState {
	count: number;
}

/** Its name is free: the core puts the reducer under the plugin id `example`, whatever it is called. */
const counterSlice = createSlice({
	name: "counter",
	initialState: { count: 0 } as ExampleState,
	reducers: {
		countUp: (state) => {
			state.count += 1;
		},
	},
});

export const exampleCountUp = counterSlice.actions.countUp;
export const exampleReducer = counterSlice.reducer;

/** Selectors start at the whole state and read the compartment under the id of the plugin. */
export const selectExampleCount = (state: AppState) => (state.example as ExampleState).count;
