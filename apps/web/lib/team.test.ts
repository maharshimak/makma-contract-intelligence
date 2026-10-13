import {describe,expect,it} from "vitest";
import {proposedCoverage} from "./team";
import type {CapabilityGap,TeamCandidate} from "./types";

const gaps=[{id:"security",gap_type:"SECURITY",severity:"CRITICAL",capability:"Cybersecurity",mandatory:true,resolution_status:"OPEN",coverage_weight:8,provenance:"SYNTHETIC_DEMO",is_demo:true},{id:"cert",gap_type:"CERTIFICATION",severity:"HIGH",capability:"ISO 27001",mandatory:true,resolution_status:"OPEN",coverage_weight:6,provenance:"SYNTHETIC_DEMO",is_demo:true},{id:"expert",gap_type:"SKILL",severity:"HIGH",capability:"French procurement expertise",mandatory:false,resolution_status:"OPEN",coverage_weight:6,provenance:"SYNTHETIC_DEMO",is_demo:true},{id:"reference",gap_type:"REFERENCE",severity:"MEDIUM",capability:"Healthcare reference",mandatory:false,resolution_status:"OPEN",coverage_weight:4,provenance:"SYNTHETIC_DEMO",is_demo:true}] satisfies CapabilityGap[];
const elena={candidate_type:"PROFESSIONAL",candidate_id:"elena",name:"Elena Martin",headline:"Architect",suitability:90,capabilities:[],resolves_gap_ids:["security","cert","expert"],is_demo:true} satisfies TeamCandidate;

describe("proposedCoverage",()=>{it("counts each resolved weighted gap once",()=>expect(proposedCoverage(76,gaps,[elena])).toBe(96));it("caps combined coverage at 100",()=>expect(proposedCoverage(96,gaps,[elena])).toBe(100))});
