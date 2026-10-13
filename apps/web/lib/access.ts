import type {Session} from "./types";

export type ProtectedArea="company"|"professional"|"admin";
export type AccessDecision={allowed:true}|{allowed:false;redirect:string};

export function authorizeArea(session:Session|null,area:ProtectedArea,nextPath:string):AccessDecision{
  if(!session)return {allowed:false,redirect:`/login?next=${encodeURIComponent(nextPath)}`};
  if(area==="admin"&&session.platform_role==="USER")return {allowed:false,redirect:"/forbidden"};
  if(area==="professional"&&!session.has_professional_profile)return {allowed:false,redirect:"/signup"};
  if(area==="company"&&!session.active_workspace)return {allowed:false,redirect:session.has_professional_profile?"/professional":"/signup"};
  return {allowed:true};
}
