import {CompanyForm} from "@/components/CompanyForm";
import {CompanyOnboardingForm} from "@/components/CompanyOnboardingForm";
import {companyCompleteness} from "@/lib/completeness";
import {api,ApiError} from "@/lib/server-api";

export const metadata={title:"Company Profile | Public Revenue OS"};

export default async function CompanyPage(){
  const session=await api.session();
  try{
    const company=await api.company();const complete=companyCompleteness(company).total;
    return <div className="content"><div className="page-header"><div><div className="eyebrow">Workspace configuration</div><h1 className="page-title">Company profile</h1><p className="subtitle">This evidence controls which opportunities enter your Revenue Radar.</p></div><span className="trust-chip">{complete}% complete</span></div><CompanyForm initial={company}/></div>;
  }catch(error){
    if(error instanceof ApiError&&error.status===404&&session.active_workspace){return <div className="content"><div className="page-header"><div><div className="eyebrow">Organization onboarding</div><h1 className="page-title">Finish organization setup</h1><p className="subtitle">Your membership is valid. This workspace simply needs a company profile before matching can begin.</p></div><span className="trust-chip">Setup required</span></div><CompanyOnboardingForm organizationName={session.active_workspace.name}/></div>}
    throw error;
  }
}
