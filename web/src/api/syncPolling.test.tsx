import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { SYNC_STATUS_INTERVAL_MS, useReloadOnAutoSync, useSyncStatuses } from "./queries";

const status = (auto: boolean, at: string | null = null) => ({
  source_id: "s1", state: "in_sync", last_sync_at: null, conflicts: 0, auto_sync: auto, auto_last_run_at: at, auto_paused: null,
});

function setup(answer: () => unknown[]) {
  const calls: string[] = [];
  vi.stubGlobal("fetch", async (request: Request) => {
    calls.push(new URL(request.url).pathname);
    return new Response(JSON.stringify(answer()), { status: 200, headers: { "Content-Type": "application/json" } });
  });
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  return { calls, client, wrapper };
}

describe("the status of the automatic sync", () => {
  beforeEach(() => vi.useFakeTimers({ shouldAdvanceTime: true }));
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });
  const count = (calls: string[]) => calls.filter((c) => c === "/api/v2/sync-status").length;

  it("is asked for again every minute while a project has the automatic sync on", async () => {
    const { calls, wrapper } = setup(() => [status(true)]);
    renderHook(() => useSyncStatuses(), { wrapper });
    await vi.waitFor(() => expect(count(calls)).toBe(1));

    await act(() => vi.advanceTimersByTimeAsync(SYNC_STATUS_INTERVAL_MS + 100));

    expect(count(calls)).toBe(2);
  });

  it("is not asked for on a timer when no project has it on, or while polling is paused", async () => {
    const off = setup(() => [status(false)]);
    renderHook(() => useSyncStatuses(), { wrapper: off.wrapper });
    await vi.waitFor(() => expect(count(off.calls)).toBe(1));
    await act(() => vi.advanceTimersByTimeAsync(SYNC_STATUS_INTERVAL_MS * 3));
    expect(count(off.calls)).toBe(1);

    const paused = setup(() => [status(true)]);
    renderHook(() => useSyncStatuses(true), { wrapper: paused.wrapper });
    await vi.waitFor(() => expect(count(paused.calls)).toBe(1));
    await act(() => vi.advanceTimersByTimeAsync(SYNC_STATUS_INTERVAL_MS * 3));
    expect(count(paused.calls)).toBe(1);
  });

  it("reads the projects and items again when a run of the automatic sync is new", () => {
    const { client, wrapper } = setup(() => []);
    const invalidate = vi.spyOn(client, "invalidateQueries");
    const { rerender } = renderHook(({ s }) => useReloadOnAutoSync(s), { wrapper, initialProps: { s: [status(true, null)] } });
    expect(invalidate).not.toHaveBeenCalled();  // the first look is no news

    rerender({ s: [status(true, null)] });
    expect(invalidate).not.toHaveBeenCalled();
    rerender({ s: [status(true, "2026-10-15T10:00:00+02:00")] });

    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["backlog"] });
  });
});
