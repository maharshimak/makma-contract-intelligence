export function ErrorState({message="The intelligence API is unavailable."}:{message?:string}){return <div className="alert"><strong>Unable to load data</strong><div className="sub">{message} Check that the API is running on port 8000 and try again.</div></div>}

