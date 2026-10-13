import {describe,expect,it} from "vitest";
import {companyCompleteness} from "./completeness";
import type {Company} from "./types";

const complete={company_name:"Makma",description:"Bid software",website:"https://example.com",siren:"123456789",siret:null,employee_count:10,annual_revenue:1,headquarters_city:"Paris",headquarters_region:"Île-de-France",headquarters_country:"FR",operating_regions:["FR"],service_categories:["Software"],technologies:["TypeScript"],certifications:["ISO 27001"],preferred_contract_min:1000,preferred_contract_max:100000,preferred_geographies:["FR"],preferred_buyer_types:["Public"],preferred_categories:["Software"],excluded_categories:[],id:"company",organization_id:"org",created_at:"",updated_at:""} satisfies Company;

describe("companyCompleteness",()=>{
  it("returns full coverage when every modeled intelligence field is present",()=>expect(companyCompleteness(complete)).toEqual({total:100,sections:{Identity:100,Capabilities:100,Preferences:100},missing:[]}));
  it("identifies missing capability evidence",()=>{const result=companyCompleteness({...complete,certifications:[],technologies:[]});expect(result.total).toBe(87);expect(result.sections.Capabilities).toBe(50);expect(result.missing).toEqual(["technologies","certifications"])});
});
