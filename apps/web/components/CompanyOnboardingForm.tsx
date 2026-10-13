"use client";

import {FormEvent,useState} from "react";
import {useRouter} from "next/navigation";
import {completeCompanyOnboarding} from "@/lib/api";

export function CompanyOnboardingForm({organizationName}:{organizationName:string}){
  const router=useRouter();
  const [error,setError]=useState("");
  const [busy,setBusy]=useState(false);
  async function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();setBusy(true);setError("");
    const data=new FormData(event.currentTarget);
    try{
      await completeCompanyOnboarding({
        company_name:String(data.get("company_name")),description:String(data.get("description"))||null,
        service_categories:String(data.get("service_categories")).split(",").map(value=>value.trim()).filter(Boolean),
        siren:null,siret:null,website:null,employee_count:null,annual_revenue:null,headquarters_city:null,
        headquarters_region:null,headquarters_country:"FR",operating_regions:[],technologies:[],certifications:[],
        preferred_contract_min:null,preferred_contract_max:null,preferred_geographies:[],preferred_buyer_types:[],
        preferred_categories:[],excluded_categories:[],
      });
      router.refresh();
    }catch(exc){setError(exc instanceof Error?exc.message:"Setup failed")}finally{setBusy(false)}
  }
  return <form onSubmit={submit} className="section"><h2>Finish organization setup</h2><p>Add the minimum information needed to activate matching for this workspace.</p><label className="field"><span>Company name</span><input name="company_name" defaultValue={organizationName} minLength={2} required/></label><label className="field"><span>Description</span><textarea name="description" required/></label><label className="field"><span>Services</span><textarea name="service_categories" placeholder="Cloud, cybersecurity, data" required/></label>{error&&<p role="alert">{error}</p>}<button className="button" disabled={busy}>{busy?"Activating workspace…":"Finish setup"}</button></form>;
}
