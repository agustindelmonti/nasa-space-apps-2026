import type { RotationExplanation } from "../data/types";

/** Sections that answer "what matters" and go up front; the rest sit in the detail. */
export const PRIMARY_SECTIONS = ["Por qué", "Riesgos", "Qué falta saber"] as const;

/** "Agua útil del perfil: Define cuánta... Cómo conseguirlo: ..." -> "Agua útil del perfil". */
const headOf = (line: string) => {
  const i = line.indexOf(":");
  return i > 0 && i < 80 ? line.slice(0, i) : line;
};

/** The fixed five-section card of the selected rotation, as the API's templates wrote it.
 *  It renders text only: every figure in it comes formatted from the backend.
 *  `part="primary"` shows the three sections that matter; `part="detail"` the other two and the extras. */
export function ExplanationCard({ card, part }: { card: RotationExplanation; part: "primary" | "detail" }) {
  const primary = part === "primary";
  const sections = Object.entries(card.sections).filter(([t]) => (PRIMARY_SECTIONS as readonly string[]).includes(t) === primary);
  if (primary) sections.sort(([a], [b]) => PRIMARY_SECTIONS.indexOf(a as never) - PRIMARY_SECTIONS.indexOf(b as never));
  const extras = primary ? [] : Object.entries(card.extras);
  return (
    <article className={primary ? "card5" : "card5-more"} aria-label="En palabras simples" data-rotation={primary ? card.rotation_id : undefined}>
      <div className={primary ? "card5-grid" : "card5-extras"}>
        {sections.map(([title, lines]) => {
          // "Qué falta saber" up front lists only the item names; the full text is in "Datos y supuestos".
          const short = primary && title === "Qué falta saber";
          return (
            <section key={title} className="card5-sec" data-section={title}>
              <h3>{title}</h3>
              {lines.length ? (
                <ul className={short ? "plain dots" : "plain"}>
                  {lines.map((l, i) => (
                    <li key={i}>{short ? headOf(l) : l}</li>
                  ))}
                </ul>
              ) : (
                <p className="soft small">Nada para informar.</p>
              )}
            </section>
          );
        })}
        {extras.map(([title, lines]) => (
          <section key={title} className="card5-sec">
            <h3>{title}</h3>
            <ul className="plain">
              {lines.map((l, i) => (
                <li key={i}>{l}</li>
              ))}
            </ul>
          </section>
        ))}
      </div>
      {!primary && <p className="small soft">{card.closing}</p>}
    </article>
  );
}
