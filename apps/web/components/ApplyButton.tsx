"use client";
import {useState} from "react";
import {api} from "@/lib/api";

export function ApplyButton({postId}:{postId:string}){const [state,setState]=useState<"idle"|"saving"|"done"|"error">("idle");async function apply(){setState("saving");try{await api.apply(postId,"Interested in contributing to this synthetic tender-linked project.");setState("done")}catch(error){setState(error instanceof Error&&error.message.includes("already")?"done":"error")}}return <button className="button" onClick={apply} disabled={state==="saving"||state==="done"}>{state==="saving"?"Applying…":state==="done"?"Application submitted":state==="error"?"Try again":"Apply to project"}</button>}
