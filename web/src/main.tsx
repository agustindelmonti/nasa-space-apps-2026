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
import { ApiDataSource } from "./data/ApiDataSource";

// With VITE_API_URL the page talks to the real engine and falls back to the fixtures if the
// API does not answer; without it, it is the offline demo. Components do not change.
const apiUrl = import.meta.env.VITE_API_URL?.trim();
const source = apiUrl ? new ApiDataSource(apiUrl, new FixtureDataSource()) : new FixtureDataSource(120);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App source={source} />
  </StrictMode>,
);
