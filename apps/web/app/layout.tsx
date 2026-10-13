import type {Metadata} from "next";
import "./globals.css";
import "./phase2.css";
import "./phase2-extra.css";
import "./phase3.css";

export const metadata:Metadata={title:{default:"Public Revenue OS",template:"%s · Public Revenue OS"},description:"Discover public-sector revenue, close capability gaps, build the team, and win."};

export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}
