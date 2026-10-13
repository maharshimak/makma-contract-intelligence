import {describe,expect,it} from "vitest";
import {journeyStageIndex} from "./journey";

describe("journeyStageIndex",()=>{
  it("maps core routes to a plain-language revenue stage",()=>{
    expect(journeyStageIndex("/app/radar")).toBe(0);
    expect(journeyStageIndex("/app/buyers/abc")).toBe(1);
    expect(journeyStageIndex("/app/opportunities/abc")).toBe(2);
    expect(journeyStageIndex("/app/team-builder/abc")).toBe(3);
    expect(journeyStageIndex("/app/pipeline")).toBe(4);
  });

  it("keeps the explorer in discovery until an opportunity is opened",()=>{
    expect(journeyStageIndex("/app/opportunities")).toBe(0);
  });
});
