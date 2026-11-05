export type ScanStep = {
  action: "wait" | "flip" | "next" | "retry" | "done";
  page: number | null;
  sheet: number | null;
  side: "front" | "back" | "either" | "";
  text: string;
  done: number;
  total: number;
};
