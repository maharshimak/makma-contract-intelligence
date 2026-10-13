import "server-only";
import {cookies} from "next/headers";
import type {ActivityEvent,AdminSummary,Application,BuyerIntel,CapabilityGap,Company,Notification,Opportunity,OpportunityPage,PipelineItem,PipelineSummary,ProcurementSourceStatus,Professional,Qualification,SavedSearch,Session,Summary,TeamRecommendation,WorkPost,Workspace} from "./types";

const API=process.env.INTERNAL_API_URL??process.env.NEXT_PUBLIC_API_URL??"http://localhost:8000";
export class ApiError extends Error{constructor(message:string,public readonly status:number){super(message)}}
async function request<T>(path:string):Promise<T>{
  const cookieStore=await cookies();
  const response=await fetch(`${API}${path}`,{headers:{Cookie:cookieStore.toString()},cache:"no-store"});
  if(!response.ok){let message=`Request failed (${response.status})`;try{const body=await response.json() as {detail?:{message?:string};error?:{message?:string}};message=body.detail?.message??body.error?.message??message}catch{}throw new ApiError(message,response.status)}
  return response.json() as Promise<T>;
}
export const api={
  summary:()=>request<Summary>("/api/dashboard/summary"),
  opportunities:(query="")=>request<OpportunityPage>(`/api/opportunities${query}`),
  opportunity:(id:string)=>request<Opportunity>(`/api/opportunities/${id}`),
  qualification:(id:string)=>request<Qualification>(`/api/opportunities/${id}/qualification`),
  company:()=>request<Company>("/api/company"),
  buyers:()=>request<BuyerIntel[]>("/api/buyers"),
  buyer:(id:string)=>request<BuyerIntel>(`/api/buyers/${id}`),
  buyerOpportunities:(id:string)=>request<OpportunityPage>(`/api/buyers/${id}/opportunities`),
  pipeline:()=>request<PipelineItem[]>("/api/pipeline"),
  pipelineSummary:()=>request<PipelineSummary>("/api/pipeline/summary"),
  savedSearches:()=>request<SavedSearch[]>("/api/saved-searches"),
  notifications:()=>request<Notification[]>("/api/notifications"),
  activity:()=>request<ActivityEvent[]>("/api/activity"),
  session:()=>request<Session>("/api/session"),
  workspaces:()=>request<Workspace[]>("/api/workspaces"),
  professional:()=>request<Professional>("/api/professionals/me"),
  professionals:()=>request<Professional[]>("/api/professionals"),
  workPosts:()=>request<WorkPost[]>("/api/work-posts"),
  applications:()=>request<Application[]>("/api/applications/me"),
  gaps:(opportunityId:string)=>request<CapabilityGap[]>(`/api/opportunities/${opportunityId}/capability-gaps`),
  teamRecommendations:(opportunityId:string)=>request<TeamRecommendation>(`/api/opportunities/${opportunityId}/team-recommendations`),
  adminSummary:()=>request<AdminSummary>("/api/admin/summary"),
  procurementSources:()=>request<ProcurementSourceStatus[]>("/api/admin/procurement/sources"),
};
