// Spanish UI labels for contract enums. Text only, no logic.
import type { Crop, WaterFeasibility } from "../data/types";

export const DATASET_LABEL: Record<string, string> = {
  NASA_POWER: "NASA POWER",
  SMAP_L4: "SMAP L4",
  GPM_IMERG: "GPM IMERG",
  GRACE_FO: "GRACE-FO",
  MODIS_NDVI: "MODIS NDVI",
  HLS_NDVI: "HLS NDVI",
  SOILGRIDS: "SoilGrids",
  GLDAS: "GLDAS",
  SRTM: "SRTM",
  ECOSTRESS: "ECOSTRESS",
  FIELD_HAMMER: "Martillador de campo",
};

export const WATER_LABEL: Record<WaterFeasibility, string> = {
  FEASIBLE: "Factible",
  RISKY: "Riesgosa",
  NOT_FEASIBLE: "No factible",
  UNKNOWN: "Desconocida",
};

export const CROP_LABEL: Record<Crop, string> = {
  SOY_1ST: "soja de primera",
  SOY_2ND: "soja de segunda",
  MAIZE_EARLY: "maíz temprano",
  MAIZE_LATE: "maíz tardío",
  WHEAT: "trigo",
  COVER_VETCH: "vicia",
  COVER_RYE: "centeno",
  COVER_OAT: "avena",
};

/** Crop series token (DESIGN.md "Series de cultivos"). */
export const CROP_SERIES: Record<Crop, string> = {
  SOY_1ST: "soy",
  SOY_2ND: "soy",
  MAIZE_EARLY: "maize",
  MAIZE_LATE: "maize",
  WHEAT: "wheat",
  COVER_VETCH: "vetch",
  COVER_RYE: "rye-oat",
  COVER_OAT: "rye-oat",
};

export const SEVERITY_LABEL = { LOW: "baja", MEDIUM: "media", HIGH: "alta" } as const;

export const RISK_LABEL: Record<string, string> = {
  WATER: "Agua",
  FROST: "Helada",
  HEAT_STRESS: "Estrés térmico",
  EXTREME_RAIN: "Lluvia extrema",
  ECONOMIC: "Económico",
  WEEDS: "Malezas",
  SOIL: "Suelo",
};

export const MONTH_INITIAL = ["E", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"];
export const MONTH_NAME = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
