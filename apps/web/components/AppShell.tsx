"use client";

import Link from "next/link";
import {usePathname,useRouter} from "next/navigation";
import {useEffect,useMemo,useState} from "react";
import {ProductGuide,ProductJourney} from "@/components/ProductJourney";
import {api} from "@/lib/api";
import {journeyStageIndex} from "@/lib/journey";
import type {Session} from "@/lib/types";

const primary=[["Revenue Radar","/app/radar"],["Opportunities","/app/opportunities"],["Pipeline","/app/pipeline"],["Buyer Intelligence","/app/buyers"],["Talent Network","/app/marketplace"]] as const;
const secondary=[["Saved searches","/app/saved"],["Alerts","/app/alerts"],["Company Profile","/app/company"]] as const;
const commands=[...primary,...secondary,["Professional Opportunity Hub","/professional"],["Network administration","/admin"],["Open public website","/"]] as const;

export function AppShell({children,session}:{children:React.ReactNode;session:Session}){
  const pathname=usePathname();const router=useRouter();const [palette,setPalette]=useState(false);const [guide,setGuide]=useState(false);const [query,setQuery]=useState("");
  const workspace=session.active_workspace;const activeJourneyStage=journeyStageIndex(pathname);
  const initials=(workspace?.name??session.display_name).split(" ").map(part=>part[0]).join("").slice(0,2).toUpperCase();
  useEffect(()=>{const handler=(event:KeyboardEvent)=>{if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==="k"){event.preventDefault();setPalette(value=>!value)}if(event.key==="Escape"){setPalette(false);setGuide(false)}};window.addEventListener("keydown",handler);return()=>window.removeEventListener("keydown",handler)},[]);
  const matches=useMemo(()=>commands.filter(([label])=>label.toLowerCase().includes(query.toLowerCase())),[query]);
  const nav=(items:ReadonlyArray<readonly [string,string]>)=>items.map(([label,href])=><Link className={pathname===href||pathname.startsWith(`${href}/`)?"active":""} href={href} key={href}>{label}</Link>);
  async function logout(){await api.logout();router.replace("/login");router.refresh()}
  async function switchWorkspace(id:string){await api.switchWorkspace(id);router.refresh()}
  return <div className="shell">
    <aside className="sidebar"><Link href="/app/radar" className="brand"><span className="brand-mark">PUBLIC REVENUE</span><span className="brand-name">OS</span><span className="brand-promise">Find it. Fit it. Win it.</span></Link><nav className="nav" aria-label="Primary navigation">{nav(primary)}<div className="nav-divider"/>{nav(secondary)}<div className="nav-divider"/><Link href="/professional">Professional Hub<small>Switch role</small></Link>{session.platform_role!=="USER"&&<Link href="/admin">Admin<small>Platform access</small></Link>}</nav><div className="org-switcher"><span className="avatar">{initials}</span><span><strong>{workspace?.name}</strong><small>{workspace?.role}{workspace?.is_demo?" · Demo workspace":""}</small></span>{session.workspaces.length>1&&<select aria-label="Active workspace" value={workspace?.id} onChange={event=>void switchWorkspace(event.target.value)}>{session.workspaces.map(item=><option value={item.id} key={item.id}>{item.name}</option>)}</select>}</div></aside>
    <main className="main"><header className="topbar"><nav className="mobile-nav" aria-label="Mobile navigation"><Link href="/app/radar">Radar</Link><Link href="/app/opportunities">Opportunities</Link><Link href="/app/marketplace">Network</Link></nav><button className="global-search" onClick={()=>setPalette(true)} aria-label="Open command palette"><span>Search opportunities, people, partners…</span><kbd>Ctrl K</kbd></button><button className="topbar-help" type="button" onClick={()=>setGuide(true)}>How it works</button><span className="environment">{session.demo_session?"DEMO · SYNTHETIC":"PRIVATE WORKSPACE"}</span><button className="topbar-help" type="button" onClick={()=>void logout()}>Sign out</button></header><ProductJourney activeIndex={activeJourneyStage} onOpenGuide={()=>setGuide(true)}/>{children}</main>
    {guide&&<ProductGuide onClose={()=>setGuide(false)}/>} 
    {palette&&<div className="palette-backdrop" role="presentation" onMouseDown={()=>setPalette(false)}><div className="palette" role="dialog" aria-modal="true" aria-label="Command palette" onMouseDown={event=>event.stopPropagation()}><input autoFocus value={query} onChange={event=>setQuery(event.target.value)} placeholder="Search pages and commands…" aria-label="Command search"/><div className="palette-results">{matches.map(([label,href])=><button key={`${label}-${href}`} onClick={()=>{setPalette(false);setQuery("");router.push(href)}}><span>{label}</span><small>{href}</small></button>)}{!matches.length&&<p>No commands found.</p>}</div></div></div>}
  </div>;
}
