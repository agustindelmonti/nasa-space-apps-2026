import { createContext, useContext } from "react";
import type { AssumptionInfo } from "../data/types";

export const AssumptionsContext = createContext<Record<string, AssumptionInfo>>({});
export const useAssumptions = () => useContext(AssumptionsContext);
