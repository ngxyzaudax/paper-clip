import type { UseQueryResult } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { StatusNote } from "./StatusNote";

type QueryGateProps<T> = {
  query: UseQueryResult<T, Error>;
  children: (data: T) => ReactNode;
  empty?: ReactNode;
  isEmpty?: (data: T) => boolean;
  loading?: string;
  errorTitle?: string;
};

export function QueryGate<T>(props: QueryGateProps<T>): ReactNode {
  const { query } = props;
  if (query.isPending) return <StatusNote tone="busy" title={props.loading ?? "Loading"} detail="One moment." />;
  if (query.isError) {
    return (
      <StatusNote
        tone="error"
        title={props.errorTitle ?? "This did not load"}
        detail={query.error.message}
        onRetry={(): void => void query.refetch()}
      />
    );
  }
  if (props.isEmpty?.(query.data)) return props.empty ?? <StatusNote tone="empty" title="Nothing here" />;
  return props.children(query.data);
}
