import { QueryClient, QueryClientProvider, focusManager } from "@tanstack/react-query";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DUE_COUNT_INTERVAL_MS, useDueCount } from "../api/queries";
import { stubRoutes } from "../test/api";
import { renderWithProviders } from "../test/render";
import { DueBadge } from "./DueBadge";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
  focusManager.setFocused(undefined);
});

describe("DueBadge", () => {
  it("is not shown at zero", () => {
    renderWithProviders(<DueBadge count={0} onOpen={vi.fn()} />);

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("shows the number and a label, and a click opens the list", async () => {
    const onOpen = vi.fn();
    renderWithProviders(<DueBadge count={3} onOpen={onOpen} />);

    const button = screen.getByRole("button", { name: "3 fällige Notes oder Hinweise" });
    expect(button).toHaveTextContent("3");
    await userEvent.click(button);
    expect(onOpen).toHaveBeenCalledTimes(1);
  });

  it("shows 99+ for a large number", () => {
    renderWithProviders(<DueBadge count={250} onOpen={vi.fn()} />);

    expect(screen.getByRole("button")).toHaveTextContent("99+");
  });

  it("follows the data: appears with a count and disappears when it falls to zero", () => {
    const { rerender } = renderWithProviders(<DueBadge count={0} onOpen={vi.fn()} />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();

    rerender(<DueBadge count={2} onOpen={vi.fn()} />);
    expect(screen.getByRole("button")).toBeInTheDocument();

    rerender(<DueBadge count={0} onOpen={vi.fn()} />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});

function Probe({ paused = false }: { paused?: boolean }) {
  const due = useDueCount(paused);
  return <div data-testid="count">{due.data?.count ?? "…"}</div>;
}

function renderProbe(paused = false) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <Probe paused={paused} />
    </QueryClientProvider>,
  );
}

describe("useDueCount", () => {
  it("asks the cheap counter route, and nothing else", async () => {
    const calls = stubRoutes([{ method: "GET", path: "/api/v2/notes/due/count", respond: () => ({ count: 4, by_project: { P: 4 } }) }]);
    renderProbe();

    expect(await screen.findByText("4")).toBeInTheDocument();
    expect(calls.map((c) => c.path)).toEqual(["/api/v2/notes/due/count"]);
  });

  it("asks again every 60 seconds", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    let count = 1;
    const calls = stubRoutes([{ method: "GET", path: "/api/v2/notes/due/count", respond: () => ({ count: count++, by_project: {} }) }]);
    renderProbe();
    await waitFor(() => expect(screen.getByTestId("count")).toHaveTextContent("1"));

    await act(async () => {
      await vi.advanceTimersByTimeAsync(DUE_COUNT_INTERVAL_MS);
    });

    await waitFor(() => expect(screen.getByTestId("count")).toHaveTextContent("2"));
    expect(calls).toHaveLength(2);
  });

  it("does not poll while polling is paused", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const calls = stubRoutes([{ method: "GET", path: "/api/v2/notes/due/count", respond: () => ({ count: 1, by_project: {} }) }]);
    renderProbe(true);
    await waitFor(() => expect(screen.getByTestId("count")).toHaveTextContent("1"));

    await act(async () => {
      await vi.advanceTimersByTimeAsync(DUE_COUNT_INTERVAL_MS * 3);
    });

    expect(calls).toHaveLength(1);
  });

  it("asks again when the window gets focus", async () => {
    let count = 1;
    const calls = stubRoutes([{ method: "GET", path: "/api/v2/notes/due/count", respond: () => ({ count: count++, by_project: {} }) }]);
    renderProbe();
    await waitFor(() => expect(screen.getByTestId("count")).toHaveTextContent("1"));

    act(() => {
      focusManager.setFocused(false);
      focusManager.setFocused(true);
    });

    await waitFor(() => expect(screen.getByTestId("count")).toHaveTextContent("2"));
    expect(calls).toHaveLength(2);
  });
});
