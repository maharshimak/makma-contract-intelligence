import Link from "next/link";

export default function ForbiddenPage(){return <main className="auth-page"><div className="auth-card"><div className="eyebrow">ACCESS DENIED</div><h1>Platform administrator access required</h1><p>Your account is authenticated, but organization ownership does not grant platform administration.</p><Link className="button" href="/app/radar">Return to workspace</Link></div></main>}
