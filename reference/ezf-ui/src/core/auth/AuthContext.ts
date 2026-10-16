import { createContext } from "react";
import type { Auth } from "./types";

/** The login of this start; without a provider there is none. */
export const AuthContext = createContext<Auth | undefined>(undefined);
