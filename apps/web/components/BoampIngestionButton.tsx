"use client";

import {useState} from "react";
import {useRouter} from "next/navigation";
import {api} from "@/lib/api";

export default function BoampIngestionButton(){
  const router=useRouter();
  const [pending,setPending]=useState(false);
  const [message,setMessage]=useState<string|null>(null);
  async function ingest(){
    setPending(true);setMessage(null);
    try{
      const result=await api.ingestBoamp(10);
      setMessage(`${result.created} created · ${result.updated} updated · ${result.unchanged} unchanged · ${result.rejected} rejected`);
      router.refresh();
    }catch(error){setMessage(error instanceof Error?error.message:"BOAMP ingestion failed");}
    finally{setPending(false);}
  }
  return <div className="ingestion-control"><button className="button" type="button" onClick={ingest} disabled={pending}>{pending?"Importing…":"Import latest 10"}</button>{message&&<small aria-live="polite">{message}</small>}</div>;
}
