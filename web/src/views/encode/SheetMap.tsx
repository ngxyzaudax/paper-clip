import type { ReactElement } from "react";
import { classes } from "../../lib/classes";
import styles from "./encode.module.css";

type Side = "data" | "parity" | "blank";
const MAX_DRAWN = 24;

export function SheetMap(props: { dataPages: number; parityPages: number; sides: number }): ReactElement {
  const sheets = layout(props.dataPages, props.parityPages, props.sides);
  const drawn = sheets.slice(0, MAX_DRAWN);
  return (
    <div className={styles.column}>
      <div className={styles.sheets} role="img" aria-label={describe(props.dataPages, props.parityPages, sheets.length)}>
        {drawn.map((sheet, index) => (
          <div key={index} className={styles.sheet} style={props.sides === 2 ? undefined : { gridTemplateColumns: "18px" }}>
            {sheet.map((side, slot) => <span key={slot} className={classes(styles.side, styles[side])} />)}
          </div>
        ))}
        {sheets.length > MAX_DRAWN ? <span>+{sheets.length - MAX_DRAWN} more</span> : null}
      </div>
      <div className={styles.legend} aria-hidden="true">
        <span><i className={styles.data} />File</span>
        {props.parityPages > 0 ? <span><i className={styles.parity} />Spare</span> : null}
        {sheets.flat().includes("blank") ? <span><i className={styles.blank} />Blank</span> : null}
      </div>
    </div>
  );
}

function layout(dataPages: number, parityPages: number, sides: number): Side[][] {
  const pages: Side[] = [...Array<Side>(dataPages).fill("data"), ...Array<Side>(parityPages).fill("parity")];
  const width = sides === 2 ? 2 : 1;
  const count = Math.max(1, Math.ceil(pages.length / width));
  return Array.from({ length: count }, (_, sheet) => Array.from({ length: width }, (_, slot) => pages[sheet * width + slot] ?? "blank"));
}

function describe(dataPages: number, parityPages: number, sheets: number): string {
  const sheetWord = sheets === 1 ? "sheet" : "sheets";
  const fileWord = dataPages === 1 ? "page for the file" : "pages for the file";
  const spareWord = parityPages === 1 ? "spare page" : "spare pages";
  return `${sheets} ${sheetWord}: ${dataPages} ${fileWord} and ${parityPages} ${spareWord}`;
}
