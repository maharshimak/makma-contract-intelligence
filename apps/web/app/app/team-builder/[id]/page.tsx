import Link from "next/link";
import {TeamBuilder} from "@/components/TeamBuilder";
import {ErrorState} from "@/components/ErrorState";
import {api} from "@/lib/server-api";
import {valueRange} from "@/lib/format";

export const metadata={title:"Build Bid Team"};
export default async function TeamBuilderPage({params}:{params:Promise<{id:string}>}){const {id}=await params;try{const [opportunity,gaps,recommendations]=await Promise.all([api.opportunity(id),api.gaps(id),api.teamRecommendations(id)]);return <div className="content wide"><div className="page-header"><div><div className="eyebrow">Tender-to-Team · Synthetic demonstration</div><h1 className="page-title">Complete your bid team</h1><p className="subtitle">{opportunity.title} · {valueRange(opportunity.estimated_value_min,opportunity.estimated_value_max)}</p></div><div className="actions"><span className="trust-chip">Human-controlled draft</span><Link className="button secondary" href={`/app/opportunities/${id}`}>Back to opportunity</Link></div></div><TeamBuilder opportunityId={id} gaps={gaps} currentCoverage={recommendations.current_coverage} candidates={recommendations.candidates}/></div>}catch(error){return <div className="content"><h1 className="page-title">Build bid team</h1><ErrorState message={error instanceof Error?error.message:undefined}/></div>}}
