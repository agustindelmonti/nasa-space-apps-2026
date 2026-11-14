import { useCallback, useEffect, useRef, useState } from "react";
import { isIgnorable, type DataSource } from "./data/DataSource";
import type { DisplayPreference, Evaluation, PlotContext, ProfileId, ProfileOverrides, YearClassFilter } from "./data/types";
import { positions, rankDiff, tableOrder, toRankMap, type RankMap } from "./lib/rankDiff";
import { AssumptionsContext } from "./components/AssumptionsContext";
import { LotMap } from "./components/LotMap";
import { WaterPanel } from "./components/WaterPanel";
import { ActorSelector } from "./components/ActorSelector";
import { ProfilePanel } from "./components/ProfilePanel";
import { Verdict } from "./components/Verdict";
import { EvaluationOptions } from "./components/EvaluationOptions";
import { RankingTable } from "./components/RankingTable";
import { EvidencePanel } from "./components/EvidencePanel";
import { AskPanel } from "./components/AskPanel";
import type { AgentClient } from "./data/AgentClient";
import { MessageCircle } from "lucide-react";

const PLOT_ID = "demo-casilda";
/** Slider moves are sent once the hand stops for this long. */
const SLIDER_DEBOUNCE_MS = 250;
let entryPlayed = false; // the strip fill plays once per session

interface Shown {
  evaluation: Evaluation;
  order: string[];
}

export function App({ source, agent }: { source: DataSource; agent?: AgentClient }) {
  const [askOpen, setAskOpen] = useState(false);
  const [ctx, setCtx] = useState<PlotContext | null>(null);
  const [profileId, setProfileId] = useState<ProfileId>("OWNER");
  const [draft, setDraft] = useState<ProfileOverrides>({});
  const [overrides, setOverrides] = useState<ProfileOverrides>({});
  const [yearClass, setYearClass] = useState<YearClassFilter>("ALL");
  const [prefs, setPrefs] = useState<DisplayPreference[]>([]);
  const [shown, setShown] = useState<Shown | null>(null);
  const [moves, setMoves] = useState<Record<string, number>>({});
  const [evaluationKey, setEvaluationKey] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const [animateEntry] = useState(() => !entryPlayed);
  const lastPositions = useRef<RankMap | null>(null);
  const debounce = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  useEffect(() => {
    entryPlayed = true;
    const ctrl = new AbortController();
    source.getContext(PLOT_ID, ctrl.signal).then(setCtx, (e: Error) => !isIgnorable(e) && setError(e.message));
    return () => ctrl.abort();
  }, [source]);

  // One request per change of actor, committed overrides, year class or preferences. Only the
  // latest one may land: the effect cleanup aborts the previous one and the source discards
  // any response that still arrives late.
  useEffect(() => {
    if (!ctx) return;
    const ctrl = new AbortController();
    setLoading(true);
    setError(null);
    source
      .evaluate({ plotId: PLOT_ID, profileId, overrides, yearClassFilter: yearClass, displayPreferences: prefs }, ctrl.signal)
      .then((evaluation) => {
        if (ctrl.signal.aborted) return;
        const order = tableOrder(evaluation.output.results, evaluation.displayOrder, prefs.length > 0);
        const now = positions(order);
        setMoves(rankDiff(lastPositions.current, now));
        lastPositions.current = toRankMap(now);
        setEvaluationKey((k) => k + 1);
        setShown({ evaluation, order });
        setSelectedId((sel) =>
          sel && evaluation.output.results.some((r) => r.rotation_id === sel) ? sel : (order[0] ?? null),
        );
        setLoading(false);
      })
      .catch((e: Error) => {
        if (isIgnorable(e) || ctrl.signal.aborted) return;
        setError(e.message);
        setLoading(false);
      });
    return () => ctrl.abort();
  }, [source, ctx, profileId, overrides, yearClass, prefs, retry]);

  useEffect(() => () => clearTimeout(debounce.current), []);

  const changeActor = useCallback((id: ProfileId) => {
    clearTimeout(debounce.current);
    setDraft({});
    setOverrides({});
    setProfileId(id);
  }, []);

  const changeSliders = useCallback((next: ProfileOverrides) => {
    setDraft(next);
    clearTimeout(debounce.current);
    debounce.current = setTimeout(() => setOverrides(next), SLIDER_DEBOUNCE_MS);
  }, []);

  const resetSliders = useCallback(() => {
    clearTimeout(debounce.current);
    setDraft({});
    setOverrides({});
  }, []);

  const evaluation = shown?.evaluation ?? null;
  const exampleData = ctx?.origin === "fixture" || evaluation?.origin === "fixture";
  const offline = source.kind === "api" && exampleData;
  const names = evaluation?.rotationNames ?? {};
  const selected = evaluation?.output.results.find((r) => r.rotation_id === selectedId) ?? null;
  const profile = ctx?.profiles.find((p) => p.profile_id === profileId);

  return (
    <AssumptionsContext.Provider value={ctx?.assumptions ?? {}}>
      <a className="skip" href="#ranking">
        Ir al ranking
      </a>
      <div className={`shell${askOpen && agent ? " has-ask" : ""}`}>
      <div className="wrap">
        <header className="top">
          <div className="brand">
            <svg className="mark" viewBox="0 0 40 40" aria-hidden="true">
              <rect x="1" y="1" width="38" height="38" fill="none" stroke="currentColor" strokeWidth="2" />
              <path d="M6 30 L34 10 M6 22 L26 8 M14 34 L34 20" stroke="currentColor" strokeWidth="2" />
            </svg>
            <h1>Rastrojo</h1>
          </div>
          <div className="lede">
            <p className="soft">Rotaciones para tu lote medidas contra 45 campañas reales de datos NASA. Cambiá quién decide y mirá cómo se reordenan.</p>
            <p className="legends">
              <span>Apoya, no reemplaza al agrónomo.</span>
              <span>Escenarios históricos, no predicción.</span>
            </p>
          </div>
          {agent && (
            <button type="button" className="btn-secondary btn-ask" aria-expanded={askOpen} onClick={() => setAskOpen((o) => !o)}>
              <MessageCircle size={20} strokeWidth={1.5} aria-hidden="true" />
              Preguntale a Rastrojo
            </button>
          )}
          {offline ? (
            <p className="example" role="status" data-mode="offline">
              Modo demo sin conexión: el motor no respondió y se muestran datos de ejemplo, no resultados del motor.
            </p>
          ) : (
            exampleData && (
              <p className="example" role="note">
                Datos de ejemplo: el ranking y las cifras no son resultados del motor.
              </p>
            )
          )}
        </header>

        {error && (
          <p className="warn" role="alert">
            No se pudo cargar la evaluación: {error}.{" "}
            <button type="button" className="btn-secondary" onClick={() => setRetry((n) => n + 1)}>
              Reintentar
            </button>
          </p>
        )}

        {ctx && (
          <main className="viewer">
            {shown && profile ? (
              <Verdict results={shown.evaluation.output.results} order={shown.order} names={names} actorLabel={profile.label}>
                <ActorSelector profiles={ctx.profiles} value={profileId} onChange={changeActor} />
              </Verdict>
            ) : (
              <section className="verdict">
                <ActorSelector profiles={ctx.profiles} value={profileId} onChange={changeActor} />
              </section>
            )}
            <div className="main-col" id="ranking">
              {shown && (
                <RankingTable
                  results={shown.evaluation.output.results}
                  names={names}
                  order={shown.order}
                  warnings={shown.evaluation.output.warnings}
                  strips={ctx.strips}
                  moves={moves}
                  evaluationKey={evaluationKey}
                  selectedId={selectedId}
                  onSelect={setSelectedId}
                  loading={loading}
                  animateEntry={animateEntry}
                  inputHash={shown.evaluation.inputHash}
                  toolbar={
                    <EvaluationOptions yearClass={yearClass} onYearClass={setYearClass} preferences={prefs} onPreferences={setPrefs} disabled={exampleData} />
                  }
                />
              )}
            </div>
            <aside className="side" aria-label="Lote, agua y perfil">
              <LotMap plot={ctx.plot} />
              <WaterPanel cells={ctx.water_panel} />
              {profile && (
                <ProfilePanel
                  profile={profile}
                  limits={ctx.slider_limits}
                  overrides={draft}
                  onChange={changeSliders}
                  onReset={resetSliders}
                  disabled={exampleData}
                />
              )}
            </aside>
            {selected && (
              <EvidencePanel
                result={selected}
                name={names[selected.rotation_id] ?? selected.rotation_id}
                card={evaluation?.explanation?.rotations.find((c) => c.rotation_id === selected.rotation_id)}
              />
            )}
          </main>
        )}
      </div>
      {askOpen && agent && <AskPanel client={agent} actor={profileId} onClose={() => setAskOpen(false)} />}
      </div>
    </AssumptionsContext.Provider>
  );
}
