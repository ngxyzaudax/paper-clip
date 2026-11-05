import type { ReactElement } from "react";
import type { EncodePlan } from "../../api/types";
import { useViewMode } from "../../components/shell/ViewModeContext";
import { FactList } from "../../components/ui/FactList";
import { Reveal } from "../../components/ui/Reveal";
import { rgbCss } from "../../lib/format";
import view from "../../styles/view.module.css";
import { inkName } from "./inkName";
import ui from "../../styles/ui.module.css";
import { planFacts, protectionText, sheetText } from "./planFacts";
import { SheetMap } from "./SheetMap";
import styles from "./encode.module.css";

export function EncodePlanCard(props: { plan: EncodePlan }): ReactElement {
  const mode = useViewMode().mode;
  return (
    <section className={ui.card} aria-label="Encoding plan">
      <div className={styles.column}>
        <div className={styles.summary}>
          <strong>{sheetText(props.plan)}</strong>
          <p>{protectionText(props.plan)}</p>
        </div>
        <SheetMap dataPages={props.plan.data_pages} parityPages={props.plan.parity_pages} sides={props.plan.sides} />
        <FactList rows={planFacts(props.plan, mode)} />
        <Reveal at="expert">
          <div className={styles.column}>
            <div className={styles.swatches} aria-label="Ink colours">
              {props.plan.palette.map((color, index) => (
                <span key={`${rgbCss(color)}-${index}`} className={styles.swatch} style={{ background: rgbCss(color) }} title={inkName(color)}>
                  <span className={ui.visuallyHidden}>{`Colour ${index + 1}, ${inkName(color)}`}</span>
                </span>
              ))}
            </div>
            <p className={view.caption}>Blank paper is a colour too, and it is not shown here.</p>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
