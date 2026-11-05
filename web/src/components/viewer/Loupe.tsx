import { useEffect, useState } from "react";
import type { MouseEvent, ReactElement } from "react";
import { useDebounced } from "../../hooks/useDebounced";
import styles from "./viewer.module.css";

const LENS_PX = 220;
const STEPS = 400;

type Point = { fx: number; fy: number; left: number; top: number };

export function Loupe(props: { crop: string; turn: number }): ReactElement {
  const [point, setPoint] = useState<Point | null>(null);
  const settled = useDebounced(point, 60);
  const [image, setImage] = useState("");
  useEffect(() => {
    if (!settled) return;
    setImage(`${props.crop}?fx=${settled.fx}&fy=${settled.fy}&w=${LENS_PX}&h=${LENS_PX}`);
  }, [settled, props.crop]);
  return (
    <div className={styles.loupeArea} onMouseMove={(event): void => setPoint(pointAt(event, props.turn))} onMouseLeave={(): void => setPoint(null)}>
      {point && image ? (
        <div className={styles.lens} style={{ left: point.left, top: point.top, width: LENS_PX, height: LENS_PX, backgroundImage: `url("${image}")` }} aria-hidden="true" />
      ) : null}
    </div>
  );
}

function pointAt(event: MouseEvent<HTMLDivElement>, turn: number): Point {
  const box = event.currentTarget.getBoundingClientRect();
  const x = (event.clientX - box.left) / box.width;
  const y = (event.clientY - box.top) / box.height;
  const flipped = turn === 180;
  const fx = Math.round((flipped ? 1 - x : x) * STEPS) / STEPS;
  const fy = Math.round((flipped ? 1 - y : y) * STEPS) / STEPS;
  const local = flipped ? { left: (1 - x) * box.width, top: (1 - y) * box.height } : { left: x * box.width, top: y * box.height };
  return { fx, fy, left: local.left - LENS_PX / 2, top: local.top - LENS_PX / 2 };
}
