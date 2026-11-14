import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@fontsource/schibsted-grotesk/latin-600.css";
import "@fontsource/schibsted-grotesk/latin-800.css";
import "@fontsource/atkinson-hyperlegible-next/latin-400.css";
import "@fontsource/atkinson-hyperlegible-next/latin-700.css";
import "@fontsource/ibm-plex-mono/latin-400.css";
import "@fontsource/ibm-plex-mono/latin-500.css";
import "./styles/tokens.css";
import "./styles/app.css";
import { App } from "./App";
import { FixtureDataSource } from "./data/FixtureDataSource";

// Swap for the API-backed DataSource when /api/v1 exists; components do not change.
const source = new FixtureDataSource(120);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App source={source} />
  </StrictMode>,
);
