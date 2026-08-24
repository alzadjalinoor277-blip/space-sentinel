import { useEffect, useRef, useState, useCallback } from 'react';

interface PollOptions {
  intervalMs?: number;
  enabled?: boolean;
}

export function usePoll<T>(fetcher: () => Promise<T>, { intervalMs = 2000, enabled = true }: PollOptions = {}) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const refetch = useCallback(async () => {
    try {
      const result = await fetcherRef.current();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    let timer: number | undefined;

    const run = async () => {
      if (cancelled) return;
      await refetch();
      if (!cancelled) timer = window.setTimeout(run, intervalMs);
    };
    run();

    return () => {
      cancelled = true;
      if (timer) window.clearTimeout(timer);
    };
  }, [enabled, intervalMs, refetch]);

  return { data, error, loading, refetch };
}
