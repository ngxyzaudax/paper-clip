import type { ReactElement } from "react";
import type { DamagePage } from "../../api/types";
import view from "../../styles/view.module.css";
import { Reveal } from "../ui/Reveal";
import { plainPage } from "../viewer/artifactPages";
import { PageViewer } from "../viewer/PageViewer";
import type { ViewerPage } from "../viewer/types";
import { Heatmap } from "./Heatmap";
import styles from "./damage.module.css";

export function DamageGallery(props: { pages: DamagePage[]; images: string[] }): ReactElement | null {
  if (props.pages.length === 0 && props.images.length === 0) return null;
  return (
    <div className={styles.column}>
      {props.images.length > 0 ? <PageViewer pages={damagePages(props.pages, props.images)} /> : null}
      <Reveal at="advanced">
        <p className={view.caption}>Each square is one area of the printed page. The top row is the top of the sheet. Darker means more of that area was misread.</p>
        <div className={styles.gallery}>
          {props.pages.map((page) => <DamageCard key={page.index} page={page} />)}
        </div>
      </Reveal>
    </div>
  );
}

function damagePages(pages: DamagePage[], images: string[]): ViewerPage[] {
  return images.map((image, index) => {
    const page = pages[index];
    return { ...plainPage(image, page ? `Page ${page.index + 1}` : `Damage ${index + 1}`), note: page ? damageNote(page) : undefined };
  });
}

function damageNote(page: DamagePage): string {
  const worst = Math.max(0, ...page.damage_map.flat());
  if (worst < 0.01) return "Under 1% of this page was misread";
  return `${page.damaged.toLocaleString()} bytes misread${page.rebuilt ? " · rebuilt from a spare page" : ""}`;
}

function DamageCard(props: { page: DamagePage }): ReactElement {
  const title = `Page ${props.page.index + 1}`;
  return (
    <article className={styles.card}>
      <h3>{title}</h3>
      <Heatmap map={props.page.damage_map} label={`${title} heatmap`} />
      <p className={styles.meta}>{damageNote(props.page)}</p>
    </article>
  );
}
