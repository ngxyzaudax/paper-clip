import { keepPreviousData, useQuery } from "@tanstack/react-query";
import type { UseQueryResult } from "@tanstack/react-query";
import { useMemo } from "react";
import { sendJson } from "../../api/client";
import type { EncodePreview, PreviewRequest } from "../../api/types";
import { useDebounced } from "../../hooks/useDebounced";

export function useEncodePreview(request: PreviewRequest): UseQueryResult<EncodePreview, Error> {
  const key = JSON.stringify(request);
  const debouncedKey = useDebounced(key, 250);
  const body = useMemo((): PreviewRequest => JSON.parse(debouncedKey) as PreviewRequest, [debouncedKey]);
  return useQuery({
    queryKey: ["encode-preview", body],
    queryFn: (): Promise<EncodePreview> => sendJson<EncodePreview>("/api/encode/preview", "POST", body),
    placeholderData: keepPreviousData,
  });
}
