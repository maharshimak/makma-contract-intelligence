"use client";

import Link from "next/link";
import {journeyStages} from "@/lib/journey";

export function ProductJourney({activeIndex,onOpenGuide}:{activeIndex:number;onOpenGuide:()=>void}){
  const active=journeyStages[activeIndex];
  return <section className="journey-shell" aria-label="Your public revenue journey">
    <div className="journey-now"><span className="journey-kicker">You are here</span><strong>{active.label}</strong><small>{active.description}</small></div>
    <div className="journey-track"><span className="journey-line"/><span className="journey-line-fill" style={{width:`${activeIndex/(journeyStages.length-1)*100}%`}}/>{journeyStages.map((stage,index)=><Link href={stage.href} className={`journey-step ${index===activeIndex?"active":""} ${index<activeIndex?"complete":""}`} aria-current={index===activeIndex?"step":undefined} key={stage.id}><span className="journey-node">{index<activeIndex?"✓":stage.number}</span><span>{stage.shortLabel}</span></Link>)}</div>
    <button className="journey-help" type="button" onClick={onOpenGuide}><span>?</span> What is this website?</button>
  </section>;
}

export function ProductGuide({onClose}:{onClose:()=>void}){
  return <div className="guide-backdrop" role="presentation" onMouseDown={onClose}><section className="guide-panel" role="dialog" aria-modal="true" aria-labelledby="guide-title" onMouseDown={event=>event.stopPropagation()}><button className="guide-close" type="button" onClick={onClose} aria-label="Close product guide">×</button><div className="guide-eyebrow">Public Revenue OS, in plain language</div><h2 id="guide-title">Turn a public need into a realistic win plan.</h2><p className="guide-lead">The website helps your company find public contracts, understand whether they fit, discover what is missing, build the right team, and keep the pursuit moving.</p><div className="guide-flow">{journeyStages.map((stage,index)=><div className="guide-stage" style={{animationDelay:`${index*80}ms`}} key={stage.id}><span>{stage.number}</span><div><strong>{stage.label}</strong><small>{stage.description}</small></div></div>)}</div><div className="guide-terms"><h3>Words you will see</h3><dl><div><dt>Match score</dt><dd>How closely an opportunity fits your company today—not a promise that you will win.</dd></div><div><dt>Buyer</dt><dd>The public organization purchasing the work.</dd></div><div><dt>Capability gap</dt><dd>A skill, certification, reference, or capacity you still need.</dd></div><div><dt>Pipeline</dt><dd>Your shortlist of opportunities and the next action for each one.</dd></div></dl></div><Link className="button guide-cta" href="/app/radar" onClick={onClose}>Start at Revenue Radar →</Link></section></div>;
}
