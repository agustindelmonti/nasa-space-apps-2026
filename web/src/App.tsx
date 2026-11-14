import { useCallback, useEffect, useRef, useState } from "react";
import type { DataSource } from "./data/DataSource";
import type { EngineOutput, PlotContext, ProfileId } from "./data/types";
import { rankDiff, toRankMap, type RankMap } from "./lib/rankDiff";
import { AssumptionsContext } from "./components/AssumptionsContext";
import { LotMap } from "./components/LotMap";
import { WaterPanel } from "./components/WaterPanel";
import { ActorSelector } from "./components/ActorSelector";
import { RankingTable } from "./components/RankingTable";
import { EvidencePanel } from "./components/EvidencePanel";

const PLOT_ID = "demo-casilda";
let entryPlayed = false; // the strip fill plays once per session

export function App({ source }: { source: DataSource }) {
  const [ctx, setCtx] = useState<PlotContext | null>(null);
  const [profileId, setProfileId] = useState<ProfileId>("OWNER");
  const [output, setOutput] = useState<EngineOutput | null>(null);
  const [moves, setMoves] = useState<Record<string, number>>({});
  const [evaluationKey, setEvaluationKey] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [animateEntry] = useState(() => !entryPlayed);
  const lastRanks = useRef<RankMap | null>(null);
  const requestSeq = useRef(0);

  useEffect(() => {
    entryPlayed = true;
    source.getContext(PLOT_ID).then(setCtx, (e: Error) => setError(e.message));
  }, [source]);

  const evaluate = useCallback(
    (id: ProfileId) => {
      const seq = ++requestSeq.current;
      setLoading(true);
      setError(null);
      source
        .evaluate({ plotId: PLOT_ID, profileId: id })
        .then((out) => {
          if (seq !== requestSeq.current) return; // a newer request superseded this one
          setMoves(rankDiff(lastRanks.current, out.results));
          lastRanks.current = toRankMap(out.results);
          setEvaluationKey((k) => k + 1);
          setOutput(out);
          setSelectedId((sel) => sel ?? out.results.find((r) => r.rank === 1)?.rotation_id ?? null);
        })
        .catch((e: Error) => seq === requestSeq.current && setError(e.message))
        .finally(() => seq === requestSeq.current && setLoading(false));
    },
    [source],
  );

  useEffect(() => evaluate(profileId), [evaluate, profileId]);

  const selected = output?.results.find((r) => r.rotation_id === selectedId) ?? null;
  const names = Object.fromEntries((ctx?.rotations ?? []).map((r) => [r.rotation_id, r.name]));

  return (
    <AssumptionsContext.Provider value={ctx?.assumptions ?? {}}>
      <a className="skip" href="#ranking">
        Ir al ranking
      </a>
      <div className="wrap">
        <header className="top">
          <div className="brand">
            <svg className="mark" viewBox="0 0 40 40" aria-hidden="true">
              <rect x="1" y="1" width="38" height="38" fill="none" stroke="currentColor" strokeWidth="2" />
              <path d="M6 30 L34 10 M6 22 L26 8 M14 34 L34 20" stroke="currentColor" strokeWidth="2" />
            </svg>
            <h1>Rastrojo</h1>
          </div>
          <p className="soft lede">
            Rotaciones para tu lote medidas contra 45 campañas reales de datos NASA. Cambiá quién decide y mirá cómo se reordenan.
          </p>
          {source.kind === "fixture" && (
            <p className="example" role="note">
              Datos de ejemplo: el ranking y las cifras no son resultados del motor.
            </p>
          )}
        </header>

        {error && (
          <p className="warn" role="alert">
            No se pudo cargar la evaluación: {error}.{" "}
            <button type="button" className="btn-secondary" onClick={() => evaluate(profileId)}>
              Reintentar
            </button>
          </p>
        )}

        {ctx && (
          <main className="viewer">
            <LotMap plot={ctx.plot} />
            <div className="panel" id="ranking">
              <WaterPanel cells={ctx.water_panel} />
              <ActorSelector profiles={ctx.profiles} value={profileId} onChange={setProfileId} />
              {output && (
                <RankingTable
                  results={output.results}
                  rotations={ctx.rotations}
                  strips={ctx.strips}
                  moves={moves}
                  evaluationKey={evaluationKey}
                  selectedId={selectedId}
                  onSelect={setSelectedId}
                  loading={loading}
                  animateEntry={animateEntry}
                />
              )}
            </div>
            {selected && <EvidencePanel result={selected} name={names[selected.rotation_id] ?? selected.rotation_id} />}
          </main>
        )}
      </div>
      <footer className="legends">
        <span>Apoya, no reemplaza al agrónomo.</span>
        <span>Escenarios históricos, no predicción.</span>
      </footer>
    </AssumptionsContext.Provider>
  );
}
