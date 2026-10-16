import { logging } from "../logging/logging";
import { createUnhandledErrors } from "./createUnhandledErrors";
import { errors } from "./errors";

/** The central reporter for unhandled errors, connected to the standard `errors` and `logging`. */
export const unhandledErrors = createUnhandledErrors({ errors, logging });
