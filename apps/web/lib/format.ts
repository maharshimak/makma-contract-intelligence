export function money(value:number|null, compact=true){if(value===null)return "Not available";return new Intl.NumberFormat("fr-FR",{style:"currency",currency:"EUR",notation:compact?"compact":"standard",maximumFractionDigits:1}).format(value)}
export function valueRange(min:number|null,max:number|null){if(min===null&&max===null)return "Not available";if(min===max||max===null)return money(min);if(min===null)return money(max);return `${money(min)} – ${money(max)}`}
export function daysLeft(deadline:string|null){if(!deadline)return null;return Math.ceil((new Date(`${deadline}T23:59:59`).getTime()-Date.now())/86400000)}
export function dateLabel(value:string|null){return value?new Intl.DateTimeFormat("fr-FR",{day:"2-digit",month:"short",year:"numeric"}).format(new Date(`${value}T12:00:00`)):"Not available"}

