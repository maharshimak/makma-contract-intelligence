import {redirect} from "next/navigation";
import {api} from "@/lib/server-api";
import {authorizeArea} from "@/lib/access";

export default async function ProfessionalLayout({children}:{children:React.ReactNode}){
  let session;try{session=await api.session()}catch{session=null}
  const decision=authorizeArea(session,"professional","/professional");if(!decision.allowed)redirect(decision.redirect);
  return children;
}
