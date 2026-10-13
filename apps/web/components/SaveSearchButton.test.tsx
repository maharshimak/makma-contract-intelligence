import {fireEvent,render,screen,waitFor} from "@testing-library/react";
import {describe,expect,it,vi} from "vitest";
import {SaveSearchButton} from "./SaveSearchButton";
import {api} from "@/lib/api";

vi.mock("@/lib/api",()=>({api:{saveSearch:vi.fn()}}));

describe("SaveSearchButton",()=>{it("persists the current URL-backed filters",async()=>{vi.mocked(api.saveSearch).mockResolvedValue({id:"s1",organization_id:"o1",name:"AI over 500k",filters:{q:"AI",min_value:"500000"},alerts_enabled:false,created_at:"2026-08-14",updated_at:"2026-08-14"});render(<SaveSearchButton filters={{q:"AI",min_value:"500000"}}/>);fireEvent.click(screen.getByRole("button",{name:"Save current view"}));fireEvent.change(screen.getByLabelText("Saved search name"),{target:{value:"AI over 500k"}});fireEvent.click(screen.getByRole("button",{name:"Save"}));await waitFor(()=>expect(api.saveSearch).toHaveBeenCalledWith("AI over 500k",{q:"AI",min_value:"500000"}));expect(screen.getByText("Search saved")).toBeInTheDocument()})});
