"use client";
export default function AppError({reset}:{error:Error&{digest?:string};reset:()=>void}){return <div className="content"><div className="alert"><strong>The workspace could not be loaded.</strong><p>The API may be unavailable or the request may have failed safely.</p><button className="button" onClick={reset}>Try again</button></div></div>}
