"use client";

import Link from "next/link";
import {useRouter} from "next/navigation";
import {FormEvent,useState} from "react";
import {api} from "@/lib/api";

export default function Signup(){
  const router=useRouter();const [type,setType]=useState<"COMPANY"|"PROFESSIONAL">("COMPANY");const [error,setError]=useState("");const [busy,setBusy]=useState(false);
  async function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();setBusy(true);setError("");const data=new FormData(event.currentTarget);
    try{await api.signup({account_type:type,email:String(data.get("email")),password:String(data.get("password")),display_name:String(data.get("display_name")),...(type==="COMPANY"?{company_name:String(data.get("company_name"))}:{})});router.replace(type==="COMPANY"?"/app/company":"/professional");router.refresh()}
    catch(exc){setError(exc instanceof Error?exc.message:"Account creation failed")}finally{setBusy(false)}
  }
  return <main className="auth-page"><div className="auth-card"><div className="eyebrow">CREATE YOUR ACCOUNT</div><h1>Choose how you work</h1><div role="group" aria-label="Account type"><button type="button" aria-pressed={type==="COMPANY"} onClick={()=>setType("COMPANY")}>Company</button><button type="button" aria-pressed={type==="PROFESSIONAL"} onClick={()=>setType("PROFESSIONAL")}>Professional</button></div><p>{type==="COMPANY"?"Create a private company workspace. You become its owner.":"Create a professional profile. No company permissions are granted."}</p><form method="post" onSubmit={submit}><label>Your name<input name="display_name" autoComplete="name" minLength={2} required/></label>{type==="COMPANY"&&<label>Company name<input name="company_name" autoComplete="organization" minLength={2} required/></label>}<label>Email<input name="email" type="email" autoComplete="email" required/></label><label>Password<input name="password" type="password" autoComplete="new-password" minLength={12} required aria-describedby="password-help"/></label><small id="password-help">At least 12 characters, including letters and numbers.</small>{error&&<p role="alert">{error}</p>}<button className="button" disabled={busy}>{busy?"Creating account…":"Create account"}</button></form><p>Already registered? <Link href="/login">Sign in</Link></p></div></main>;
}
