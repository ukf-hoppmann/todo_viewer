import { logging } from "../logging/logging";
import { modals } from "../modals/modals";
import { createErrors } from "./createErrors";

/**
 * The central object for reported errors, connected to the standard `logging`
 * and `modals`. Callable from anywhere: `errors.forOrigin(origin)(input)`.
 */
export const errors = createErrors({ logging, modals });
