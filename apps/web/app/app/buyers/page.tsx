import Link from "next/link";
import {api} from "@/lib/server-api";
import {money} from "@/lib/format";
import {ErrorState} from "@/components/ErrorState";

export const metadata={title:"Buyer Intelligence"};

export default async function Buyers(){
  try{
    const allBuyers=await api.buyers();
    const buyers=allBuyers.filter(buyer=>buyer.opportunity_count>0);
    const visibleValue=buyers.reduce((sum,buyer)=>sum+Number(buyer.combined_visible_value),0);
    const openDemand=buyers.reduce((sum,buyer)=>sum+buyer.active_opportunities,0);
    return <div className="content buyer-page">
      <div className="page-header"><div><div className="eyebrow">Step 2 · Understand the buyer</div><h1 className="page-title">See who is buying—and what they need.</h1><p className="subtitle">Each card turns procurement records into a simple picture of visible demand. Open one to see its opportunities.</p></div><span className="trust-chip">Observed data only</span></div>

      <section className="explain-card"><div className="explain-icon"><span>2</span><i/></div><div><small>Why this page matters</small><h2>Good opportunities start with buyer context.</h2><p>Use value, activity, and repeated categories to choose which public organizations deserve your attention. We show only facts currently visible in the data.</p></div><div className="explain-actions"><span><b>1</b> Pick a buyer</span><span><b>2</b> Check its demand</span><span><b>3</b> Open an opportunity</span></div></section>

      <section className="buyer-summary" aria-label="Buyer intelligence summary"><div><span className="summary-orb mint">◎</span><small>Buyers with visible demand</small><strong>{buyers.length}</strong><p>Public organizations you can explore now</p></div><div><span className="summary-orb lime">€</span><small>Visible opportunity value</small><strong>{money(visibleValue)}</strong><p>Midpoint of values supplied by the source</p></div><div><span className="summary-orb amber">↗</span><small>Open opportunities</small><strong>{openDemand}</strong><p>Current routes into public-sector revenue</p></div></section>

      <div className="section-label"><div><span className="live-pulse"/>Buyer map</div><small>Select a card to understand the buyer</small></div>
      <div className="buyer-grid buyer-grid-guided">{buyers.map((buyer,index)=><Link href={`/app/buyers/${buyer.id}`} className="buyer-card buyer-card-guided" style={{animationDelay:`${Math.min(index,8)*55}ms`}} key={buyer.id}><div className="buyer-card-top"><span className="badge status">{buyer.buyer_type??"Public buyer"}</span><span className={`source-pill ${buyer.source==="DEMO"?"demo":"live"}`}>{buyer.source==="DEMO"?"Demo":"Live source"}</span></div><h3>{buyer.name}</h3><span className="sub">{[buyer.city,buyer.region].filter(Boolean).join(", ")||"Location not supplied"}</span><div className="buyer-signal"><div><small>Visible value</small><strong>{money(buyer.combined_visible_value)}</strong></div><div><small>Open</small><strong>{buyer.active_opportunities}</strong></div></div><div className="buyer-needs"><small>What they are buying</small><div className="tags">{buyer.categories_observed.slice(0,4).map(category=><span className="tag" key={category}>{category}</span>)}</div></div><span className="card-next">Explore this buyer <b>→</b></span></Link>)}</div>
    </div>;
  }catch(error){return <div className="content"><h1 className="page-title">Buyer intelligence</h1><ErrorState message={error instanceof Error?error.message:undefined}/></div>}
}
