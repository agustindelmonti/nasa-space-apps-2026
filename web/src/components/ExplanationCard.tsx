import type { RotationExplanation } from "../data/types";

/** The fixed five-section card of the selected rotation, as the API's templates wrote it.
 *  It renders text only: every figure in it comes formatted from the backend. */
export function ExplanationCard({ card }: { card: RotationExplanation }) {
  const extras = Object.entries(card.extras);
  return (
    <article className="card5" aria-labelledby="h-card5" data-rotation={card.rotation_id}>
      <h3 id="h-card5" className="label">
        En palabras simples
      </h3>
      <div className="card5-grid">
        {Object.entries(card.sections).map(([title, lines]) => (
          <section key={title} className="card5-sec" data-section={title}>
            <h4>{title}</h4>
            {lines.length ? (
              <ul className="plain">
                {lines.map((l, i) => (
                  <li key={i}>{l}</li>
                ))}
              </ul>
            ) : (
              <p className="soft small">Nada para informar.</p>
            )}
          </section>
        ))}
      </div>
      {extras.length > 0 && (
        <div className="card5-extras">
          {extras.map(([title, lines]) => (
            <section key={title} className="card5-sec">
              <h4>{title}</h4>
              <ul className="plain">
                {lines.map((l, i) => (
                  <li key={i}>{l}</li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      )}
      <p className="small soft">{card.closing}</p>
    </article>
  );
}
