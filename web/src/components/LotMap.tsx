import { useEffect, useMemo, useState } from "react";
import { MapContainer, TileLayer, Polygon, Tooltip, ScaleControl, ImageOverlay, AttributionControl, useMap } from "react-leaflet";
import type { LatLngBoundsExpression, LatLngExpression } from "leaflet";
import { CloudRain, Droplets, Maximize2, Minimize2, Satellite, ScanLine } from "lucide-react";
import "leaflet/dist/leaflet.css";
import layers from "../config/layers.json";
import type { Plot } from "../data/types";
import { formatDate, formatNumber } from "../lib/format";

const ICONS = { satellite: Satellite, droplets: Droplets, "scan-line": ScanLine, "cloud-rain": CloudRain } as const;
type Overlay = (typeof layers.overlays)[number];

const gibsUrl = (o: Overlay) =>
  layers.gibsTemplate
    .replace("{layer}", o.gibsLayer)
    .replace("{time}", o.date)
    .replace("{tileMatrixSet}", o.tileMatrixSet)
    .replace("{ext}", o.format);

const dms = (v: number, pos: string, neg: string) => {
  const a = Math.abs(v);
  const d = Math.floor(a);
  const m = Math.round((a - d) * 60);
  return `${d}°${String(m).padStart(2, "0")}′ ${v < 0 ? neg : pos}`;
};

/** Leaflet measures its box once; tell it when the box changes size (compact <-> enlarged). */
function Resize({ large }: { large: boolean }) {
  const map = useMap();
  useEffect(() => {
    const t = setTimeout(() => map.invalidateSize(), 50);
    return () => clearTimeout(t);
  }, [map, large]);
  return null;
}

let outlineDrawn = false; // entry moment runs once per session

interface Props {
  plot: Plot;
}

export function LotMap({ plot }: Props) {
  const [active, setActive] = useState<string>("base");
  const [opacity, setOpacity] = useState(0.7);
  const [baseErrors, setBaseErrors] = useState(0);
  const [large, setLarge] = useState(false);
  useEffect(() => {
    if (!large) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setLarge(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [large]);
  const [drawOutline] = useState(() => {
    const first = !outlineDrawn;
    outlineDrawn = true;
    return first;
  });

  const ring: LatLngExpression[] = useMemo(
    () => (plot.polygon?.coordinates[0] ?? []).map(([lon, lat]) => [lat, lon] as [number, number]),
    [plot],
  );
  const center: LatLngExpression = [plot.location.lat, plot.location.lon];
  const overlay = layers.overlays.find((o) => o.id === active);
  const useFallback = baseErrors >= 4;

  const info = overlay
    ? `${overlay.dataset} · ${overlay.resolution} · ${overlay.granularity}, fecha pedida ${formatDate(overlay.date)} · ${overlay.limitation}`
    : `${layers.base.dataset} · ${layers.base.resolution} · ${layers.base.limitation}`;

  const chips = [
    { id: "base", label: layers.base.label, icon: layers.base.icon },
    ...layers.overlays.map((o) => ({ id: o.id, label: o.label, icon: o.icon })),
  ];

  return (
    <section className={`map${large ? " is-large" : ""}`} aria-labelledby="h-map">
      <div className="maptop">
        <h2 id="h-map" className="label">
          {plot.name}
        </h2>
        <button type="button" className="icon-btn map-size" aria-pressed={large} onClick={() => setLarge((v) => !v)}>
          {large ? <Minimize2 size={18} strokeWidth={1.5} aria-hidden="true" /> : <Maximize2 size={18} strokeWidth={1.5} aria-hidden="true" />}
          <span>{large ? "Achicar" : "Ampliar"}</span>
        </button>
        <div className="layers" role="group" aria-label="Capa sobre la imagen">
          {chips.map((c) => {
            const Icon = ICONS[c.icon as keyof typeof ICONS];
            return (
              <button key={c.id} type="button" data-layer={c.id} aria-pressed={active === c.id} onClick={() => setActive(c.id)}>
                <Icon size={16} strokeWidth={1.5} aria-hidden="true" />
                {c.label}
              </button>
            );
          })}
        </div>
      </div>
      <div className="map-canvas">
        <MapContainer center={center} zoom={15} minZoom={5} maxZoom={17} scrollWheelZoom={false} attributionControl={false} className="leaflet-host">
          {useFallback ? (
            <ImageOverlay url={layers.staticFallback.url} bounds={layers.staticFallback.bounds as LatLngBoundsExpression} />
          ) : (
            <TileLayer
              url={layers.base.url}
              maxNativeZoom={layers.base.maxNativeZoom}
              maxZoom={17}
              attribution={layers.base.attribution}
              eventHandlers={{ tileerror: () => setBaseErrors((n) => n + 1) }}
            />
          )}
          {overlay && (
            <TileLayer
              key={overlay.id}
              url={gibsUrl(overlay)}
              maxNativeZoom={overlay.maxNativeZoom}
              maxZoom={17}
              opacity={opacity}
              className="overlay-fade"
              attribution={`${overlay.dataset}: NASA GIBS`}
            />
          )}
          {ring.length > 0 && (
            <Polygon
              positions={ring}
              pathOptions={{ color: "#D8B46A", weight: 2, fillColor: "#D8B46A", fillOpacity: 0.12, className: drawOutline ? "lot-outline draw" : "lot-outline" }}
            >
              <Tooltip permanent direction="right" offset={[24, -20]} className="lot-label" interactive={false}>
                <span className="lot-label-title">
                  LOTE DEMO · ≈{formatNumber(plot.area_ha.value)} ha
                </span>
                <span className="lot-label-coords">
                  {dms(plot.location.lat, "N", "S")} {dms(plot.location.lon, "E", "O")}
                </span>
              </Tooltip>
            </Polygon>
          )}
          <Resize large={large} />
          <ScaleControl position="bottomleft" imperial={false} />
          <AttributionControl prefix={'<a href="https://leafletjs.com">Leaflet</a>'} />
        </MapContainer>
        {useFallback && <span className="cached-tag">Imagen cacheada · Sentinel-2 cloudless 2020</span>}
      </div>
      {overlay && (
        <div className="opacity">
          <label htmlFor="opacity">Opacidad de {overlay.label}</label>
          <input
            id="opacity"
            type="range"
            min={0.2}
            max={1}
            step={0.1}
            value={opacity}
            onChange={(e) => setOpacity(Number(e.target.value))}
            aria-valuetext={`${formatNumber(opacity * 100)} %`}
          />
          <span className="fig fig-sm">{formatNumber(opacity * 100)} %</span>
        </div>
      )}
      <div className="mapfoot">
        <span id="layerinfo" aria-live="polite">
          {info}
        </span>
        <span className="fig fig-xs">
          {layers.base.attributionShort}
          {overlay ? " · NASA GIBS" : ""}
        </span>
      </div>
    </section>
  );
}
