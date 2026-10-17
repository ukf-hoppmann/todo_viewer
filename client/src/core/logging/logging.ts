import { ConsoleSink } from "./ConsoleSink";
import { createLogging } from "./createLogging";

/**
 * The central logging object of the application. Until `configure` is called
 * the console shows everything in development and warnings and errors
 * otherwise; earlier entries are remembered for the configured levels.
 */
export const logging = createLogging();

logging.addSink(new ConsoleSink(), { level: import.meta.env.DEV ? "debug" : "warn" });
