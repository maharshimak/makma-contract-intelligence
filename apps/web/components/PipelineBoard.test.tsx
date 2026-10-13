import {fireEvent,render,screen,waitFor} from "@testing-library/react";
import {beforeEach,describe,expect,it,vi} from "vitest";
import {PipelineBoard} from "./PipelineBoard";
import {api} from "@/lib/api";
import type {PipelineItem} from "@/lib/types";

vi.mock("@/lib/api",()=>({api:{updatePipeline:vi.fn()}}));

const item={id:"pipeline-1",organization_id:"org-1",opportunity_id:"opp-1",stage:"review",value:500000,probability:25,next_action:"Review evidence",next_action_date:null,notes:null,created_at:"2026-08-14",updated_at:"2026-08-14",opportunity:{id:"opp-1",source:"DEMO",external_id:"D-1",title:"AI knowledge platform",description:null,publication_date:"2026-08-01",deadline:"2026-09-01",estimated_value_min:400000,estimated_value_max:600000,currency:"EUR",cpv_codes:[],categories:[],technologies:[],certifications_required:[],location:"Paris",region:"Île-de-France",country:"FR",contract_duration_months:12,procedure_type:"Open",source_url:null,status:"discovered",is_demo:true,buyer:{id:"buyer-1",source:"DEMO",external_id:"B-1",name:"Demo Buyer",buyer_type:"hospital",description:null,city:"Paris",region:"Île-de-France",country:"FR",website:null},match:{total_score:91,technical_score:30,geography_score:15,value_score:20,sector_score:15,buyer_score:10,eligibility_score:1,positive_reasons:[],risk_reasons:[],missing_requirements:[],scoring_version:"v0.1-deterministic",calculated_at:"2026-08-14",priority:"high"}}} satisfies PipelineItem;

describe("PipelineBoard",()=>{beforeEach(()=>vi.clearAllMocks());it("moves a pursuit through a persisted stage update",async()=>{vi.mocked(api.updatePipeline).mockResolvedValue({...item,stage:"qualified"});render(<PipelineBoard initial={[item]}/>);fireEvent.change(screen.getByLabelText("Stage for AI knowledge platform"),{target:{value:"qualified"}});await waitFor(()=>expect(api.updatePipeline).toHaveBeenCalledWith("pipeline-1",{stage:"qualified"}));expect(screen.getByLabelText("Stage for AI knowledge platform")).toHaveValue("qualified")})});
