export type JourneyStage={
  id:"discover"|"understand"|"qualify"|"assemble"|"pursue";
  number:number;
  label:string;
  shortLabel:string;
  description:string;
  href:string;
};

export const journeyStages:readonly JourneyStage[]=[
  {id:"discover",number:1,label:"Find the money",shortLabel:"Discover",description:"See relevant public opportunities and deadlines.",href:"/app/radar"},
  {id:"understand",number:2,label:"Understand the buyer",shortLabel:"Understand",description:"Learn who is buying and what demand is visible.",href:"/app/buyers"},
  {id:"qualify",number:3,label:"Decide if you can win",shortLabel:"Qualify",description:"Review fit, value, risks, and missing requirements.",href:"/app/opportunities"},
  {id:"assemble",number:4,label:"Close the gaps",shortLabel:"Build team",description:"Add the people or partners needed to deliver.",href:"/app/marketplace"},
  {id:"pursue",number:5,label:"Move toward a win",shortLabel:"Pursue",description:"Track the opportunity and the next commercial action.",href:"/app/pipeline"},
];

export function journeyStageIndex(pathname:string):number{
  if(pathname.startsWith("/app/pipeline"))return 4;
  if(pathname.startsWith("/app/team-builder")||pathname.startsWith("/app/marketplace"))return 3;
  if(pathname.startsWith("/app/buyers"))return 1;
  if(/^\/app\/opportunities\/.+/.test(pathname)||pathname.startsWith("/app/company"))return 2;
  return 0;
}
