import Link from "next/link";
import BoampIngestionButton from "@/components/BoampIngestionButton";
import {api} from "@/lib/server-api";

export const metadata={title:"Public Revenue OS Administration"};

export default async function AdminPage(){
  const [summary,sources]=await Promise.all([api.adminSummary(),api.procurementSources()]);
  return <main className="admin-shell">
    <header className="role-header admin-header"><Link href="/" className="marketing-logo"><span>PUBLIC REVENUE</span> OS Admin</Link><nav><Link href="/app/radar">Exit admin</Link></nav><div className="role-persona"><span>PA</span><div><strong>Platform Admin</strong><small>Protected demo role</small></div></div></header>
    <div className="role-content">
      <div className="page-header"><div><div className="eyebrow">Platform operations</div><h1 className="page-title">Procurement control plane</h1><p className="subtitle">Live-source health, provenance, data quality, and protected ingestion.</p></div><span className="trust-chip">ADMIN · DEMO AUTH</span></div>
      <section className="metrics admin-metrics"><div className="metric primary"><div className="metric-label">Demo users</div><div className="metric-value">{summary.users}</div></div><div className="metric"><div className="metric-label">Organizations</div><div className="metric-value">{summary.organizations}</div></div><div className="metric"><div className="metric-label">Professionals</div><div className="metric-value">{summary.professionals}</div></div><div className="metric"><div className="metric-label">Opportunities</div><div className="metric-value">{summary.procurement_records}</div></div><div className="metric"><div className="metric-label">Open work posts</div><div className="metric-value">{summary.open_work_posts}</div></div></section>
      <div className="admin-grid"><section className="section"><div className="section-heading"><div><div className="eyebrow">Source operations</div><h2>Procurement ingestion</h2></div><BoampIngestionButton/></div>{sources.map(source=><div className="ops-row source-ops-row" key={source.source}><strong>{source.source}</strong><span>{source.implemented?`${source.raw_records} raw · ${source.opportunities} normalized`:"Roadmap adapter"}</span><span className={`badge ${source.latest_run?.status==="FAILED"?"risk":"status"}`}>{source.latest_run?.status??(source.implemented?"Ready":"Not implemented")}</span>{source.latest_run&&<small>Last run: {source.latest_run.fetched} fetched, {source.latest_run.rejected} rejected</small>}</div>)}</section><section className="section"><h2>Trust controls</h2><ul className="reason-list"><li>Every changed source payload is retained with a SHA-256 fingerprint</li><li>Source identity and normalization version are queryable</li><li>Only platform administrators can trigger ingestion</li><li>Invalid records are retained and marked rejected—never fabricated</li><li>Cross-source records are never silently merged</li></ul></section></div>
    </div>
  </main>;
}
