import type {CapabilityGap,TeamCandidate} from "./types";

export function proposedCoverage(current:number,gaps:CapabilityGap[],candidates:TeamCandidate[]):number{const resolved=new Set(candidates.flatMap(candidate=>candidate.resolves_gap_ids));return Math.min(100,current+gaps.filter(gap=>resolved.has(gap.id)).reduce((sum,gap)=>sum+gap.coverage_weight,0))}
