import { Fragment, type ReactNode } from "react";

/** Renders the template markup the API uses (`**bold**` on the web, `*bold*` on WhatsApp) as
 *  <strong>, and drops `## ` heading marks. Text only: nothing is computed here. */
export function richText(text: string): ReactNode {
  const lines = text.split("\n");
  return lines.map((line, li) => {
    const clean = line.replace(/^#{1,6}\s+/, "");
    const parts = clean.split(/(\*\*[^*]+\*\*|\*[^*\s][^*]*\*)/g).filter(Boolean);
    return (
      <Fragment key={li}>
        {parts.map((p, i) =>
          /^\*\*[^*]+\*\*$/.test(p) ? <strong key={i}>{p.slice(2, -2)}</strong> : /^\*[^*]+\*$/.test(p) ? <strong key={i}>{p.slice(1, -1)}</strong> : <Fragment key={i}>{p}</Fragment>,
        )}
        {li < lines.length - 1 && <br />}
      </Fragment>
    );
  });
}
