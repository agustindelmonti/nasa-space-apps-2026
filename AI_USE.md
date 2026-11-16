# Use of AI in this project

Transparency statement for the NASA Space Apps Challenge 2026 judges (Rosario local event).

## Tools we used

- **Claude Code (Anthropic)** as an engineering assistant: writing specs with OpenSpec, implementing code, tests and documentation, always under team review.

## Where there is NO AI

- **The decision engine is 100% deterministic.** It uses no language models, no randomness and no network. Same input, same output, byte for byte (tests verify this).
- **Explanations are generated from deterministic templates** based on the engine output. Every number in the text comes from a dataset, from user input or from a flagged assumption.

## Where there CAN be AI in the product

- **"Ask Rastrojo" agent**, in two iterations. The first (default) runs on deterministic rules, with no language model. The second, optional, uses Claude (Anthropic) to understand open questions, but it can only answer with what the read-only tools over the engine return; a guard rejects any number that does not come from those tools and, on any failure, it falls back to the rule-based brain. Every answer shows the trace of tools used so it can be verified.
- **Optional layer on the WhatsApp channel**, off by default, that only rephrases the template text to make it more conversational. It has guards: it cannot add or change numbers, crops or recommendations; on any violation or error the original template is used.

## Data

- No agronomic or economic data is invented. Every value that does not come from a NASA dataset or from the user is recorded as an assumption in `docs/assumptions.md`, with a source or the mark "pending AFA".
