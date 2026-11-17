import { useLocation } from "react-router";
import { locationTestId } from "./locationTestId";

/** Shows the current address of the router, so a test can see where the app navigated to. */
export function LocationProbe() {
	const { pathname, search } = useLocation();
	return <span data-testid={locationTestId}>{pathname + search}</span>;
}
