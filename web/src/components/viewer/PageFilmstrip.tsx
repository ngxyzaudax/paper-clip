import type { ReactElement } from "react";
import { classes } from "../../lib/classes";
import type { ViewerPage } from "./types";
import styles from "./viewer.module.css";

export function PageFilmstrip(props: { pages: ViewerPage[]; index: number; onSelect: (index: number) => void }): ReactElement | null {
  if (props.pages.length < 2) return null;
  return (
    <div className={styles.film} role="list" aria-label="Pages">
      {props.pages.map((page, index) => (
        <button
          key={`${page.src}-${index}`}
          type="button"
          role="listitem"
          className={classes(styles.thumb, index === props.index && styles.current)}
          aria-current={index === props.index ? "true" : undefined}
          aria-label={page.note ? `${page.label}, ${page.note}` : page.label}
          onClick={(): void => props.onSelect(index)}
        >
          <img src={page.thumb ?? page.src} alt="" loading="lazy" style={page.rotation ? { transform: `rotate(${page.rotation}deg)` } : undefined} />
          <span>{page.label}</span>
          {page.note ? <span className={styles.note}>{page.note}</span> : null}
        </button>
      ))}
    </div>
  );
}
