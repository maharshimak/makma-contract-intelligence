import {describe,expect,it} from "vitest";
import {authorizeArea} from "./access";
import type {Session} from "./types";

const base:Session={user_id:"user",email:"user@example.com",display_name:"User",platform_role:"USER",active_workspace:null,workspaces:[],has_professional_profile:false,company_profile_complete:false,onboarding_required:false,demo_session:false};

describe("route authorization UX",()=>{
  it("redirects anonymous and expired sessions to login",()=>{
    expect(authorizeArea(null,"company","/app/radar")).toEqual({allowed:false,redirect:"/login?next=%2Fapp%2Fradar"});
  });
  it("keeps organization owners out of platform administration",()=>{
    expect(authorizeArea({...base,active_workspace:{id:"org",name:"Org",slug:"org",role:"OWNER",organization_type:"SUPPLIER",is_demo:false}},"admin","/admin")).toEqual({allowed:false,redirect:"/forbidden"});
  });
  it("separates company and professional onboarding",()=>{
    expect(authorizeArea(base,"company","/app/radar")).toEqual({allowed:false,redirect:"/signup"});
    expect(authorizeArea(base,"professional","/professional")).toEqual({allowed:false,redirect:"/signup"});
    expect(authorizeArea({...base,has_professional_profile:true},"company","/app/radar")).toEqual({allowed:false,redirect:"/professional"});
  });
  it("allows only the matching authenticated contexts",()=>{
    const professional={...base,has_professional_profile:true};
    const admin={...base,platform_role:"ADMIN" as const};
    expect(authorizeArea(professional,"professional","/professional")).toEqual({allowed:true});
    expect(authorizeArea(admin,"admin","/admin")).toEqual({allowed:true});
  });
});
