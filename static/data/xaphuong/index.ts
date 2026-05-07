import provincesData from "./provinces.json";
import wardsData from "./wards.json";
import type { Province, Ward } from "../types";

/**
 * All Vietnamese provinces and centrally-administered municipalities.
 * Sorted by province ID (BNV code).
 */
export const provinces = provincesData as Province[];

/**
 * All Vietnamese wards (phường/xã/thị trấn), linked to their parent province via provinceId.
 */
export const wards = wardsData as Ward[];
