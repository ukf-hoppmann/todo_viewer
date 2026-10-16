import { createSlice } from "@reduxjs/toolkit";
import type { AppState } from "../../../core";

interface ExampleState {
	events: number;
	count: number;
}

/** Its name is free: the core puts the reducer under the plugin id `example`, whatever it is called. */
const exampleSlice = createSlice({
	name: "example",
	initialState: { events: 0, count: 0 } as ExampleState,
	reducers: {
		eventSeen: (state) => {
			state.events += 1;
		},
		countUp: (state) => {
			state.count += 1;
		},
	},
});

export const exampleEventSeen = exampleSlice.actions.eventSeen;
export const exampleCountUp = exampleSlice.actions.countUp;
export const exampleReducer = exampleSlice.reducer;

/** Selectors start at the whole state and read the compartment under the id of the plugin. */
export const selectExampleEvents = (state: AppState) => (state.example as ExampleState).events;
export const selectExampleCount = (state: AppState) => (state.example as ExampleState).count;
