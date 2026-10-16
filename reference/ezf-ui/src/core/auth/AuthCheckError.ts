/** Why the check of the login failed: the backend cannot be reached, or it answered something unexpected. */
export type AuthCheckErrorKind = "unreachable" | "unexpected";

/** The state of the login could not be found out; the application must not start. */
export class AuthCheckError extends Error {
	readonly kind: AuthCheckErrorKind;

	constructor(kind: AuthCheckErrorKind, description: string, cause?: unknown) {
		super(`${kind}: ${description}`, { cause });
		this.name = "AuthCheckError";
		this.kind = kind;
	}
}
