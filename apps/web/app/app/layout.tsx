import {AppShell} from "@/components/AppShell";
import {redirect} from "next/navigation";
import {api} from "@/lib/server-api";
import {authorizeArea} from "@/lib/access";

export default async function ApplicationLayout({children}:{children:React.ReactNode}){
  let session;try{session=await api.session()}catch{session=null}
  const decision=authorizeArea(session,"company","/app/radar");if(!decision.allowed)redirect(decision.redirect);
  return <AppShell session={session!}>{children}</AppShell>;
}
