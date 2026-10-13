"use client";

import Link from "next/link";
import {useRouter,useSearchParams} from "next/navigation";
import {FormEvent,Suspense,useState} from "react";
import {api} from "@/lib/api";

function LoginForm(){
  const router=useRouter();const search=useSearchParams();const [error,setError]=useState("");const [busy,setBusy]=useState(false);
  async function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();setBusy(true);setError("");const data=new FormData(event.currentTarget);
    try{await api.login(String(data.get("email")),String(data.get("password")));router.replace(search.get("next")||"/app/radar");router.refresh()}
    catch(exc){setError(exc instanceof Error?exc.message:"Sign in failed")}finally{setBusy(false)}
  }
  async function demo(persona:"company"|"professional"){
    setBusy(true);setError("");
    try{await api.demoLogin(persona);router.replace(persona==="professional"?"/professional":"/app/radar");router.refresh()}
    catch(exc){setError(exc instanceof Error?exc.message:"Demo is unavailable")}finally{setBusy(false)}
  }
  return <main className="auth-page"><div className="auth-card"><div className="eyebrow">SECURE ACCESS</div><h1>Welcome back</h1><p>Sign in to your private company workspace or professional profile.</p><form method="post" onSubmit={submit}><label>Email<input name="email" type="email" autoComplete="email" required/></label><label>Password<input name="password" type="password" autoComplete="current-password" required/></label>{error&&<p role="alert">{error}</p>}<button className="button" disabled={busy}>{busy?"Signing in…":"Sign in"}</button></form><p>New here? <Link href="/signup">Create an account</Link></p>{process.env.NEXT_PUBLIC_DEMO_MODE==="true"&&<div><p>Synthetic local demo</p><button onClick={()=>void demo("company")} disabled={busy}>Company demo</button><button onClick={()=>void demo("professional")} disabled={busy}>Professional demo</button></div>}<Link href="/">Return to website</Link></div></main>;
}

export default function Login(){return <Suspense fallback={<main className="auth-page"><div className="auth-card">Loading secure sign-in…</div></main>}><LoginForm/></Suspense>}
