import type {Company} from "./types";

type ProfileField=keyof Company;
const sections={
  Identity:["company_name","description","website","siren","headquarters_city","headquarters_region"],
  Capabilities:["service_categories","technologies","certifications","operating_regions"],
  Preferences:["preferred_contract_min","preferred_contract_max","preferred_geographies","preferred_buyer_types","preferred_categories"],
} satisfies Record<string,ProfileField[]>;

function isPresent(value:Company[ProfileField]):boolean{
  if(Array.isArray(value))return value.length>0;
  return value!==null&&value!==undefined&&value!=="";
}

export interface CompletenessResult{
  total:number;
  sections:Record<keyof typeof sections,number>;
  missing:ProfileField[];
}

export function companyCompleteness(company:Company):CompletenessResult{
  const all=Object.values(sections).flat();
  const missing=all.filter(field=>!isPresent(company[field]));
  const score=(fields:ProfileField[])=>Math.round(fields.filter(field=>isPresent(company[field])).length/fields.length*100);
  return {
    total:Math.round((all.length-missing.length)/all.length*100),
    sections:{Identity:score(sections.Identity),Capabilities:score(sections.Capabilities),Preferences:score(sections.Preferences)},
    missing,
  };
}
