import {fireEvent,render,screen,waitFor} from "@testing-library/react";
import {expect,it,vi} from "vitest";
import {AppShell} from "./AppShell";
import {api} from "@/lib/api";
import type {Session} from "@/lib/types";

const replace=vi.fn();const refresh=vi.fn();
vi.mock("next/navigation",()=>({usePathname:()=>"/app/radar",useRouter:()=>({replace,refresh,push:vi.fn()})}));
vi.mock("@/components/ProductJourney",()=>({ProductJourney:()=>null,ProductGuide:()=>null}));
vi.mock("@/lib/journey",()=>({journeyStageIndex:()=>0}));
vi.mock("@/lib/api",()=>({api:{logout:vi.fn(),switchWorkspace:vi.fn()}}));

const workspaceA={id:"org-a",name:"Organization A",slug:"org-a",role:"OWNER",organization_type:"SUPPLIER",is_demo:false};
const workspaceB={...workspaceA,id:"org-b",name:"Organization B",slug:"org-b"};
const session:Session={user_id:"user",email:"owner@example.com",display_name:"Owner",platform_role:"USER",active_workspace:workspaceA,workspaces:[workspaceA,workspaceB],has_professional_profile:false,company_profile_complete:true,onboarding_required:false,demo_session:false};

it("switches only through the authenticated session API and revokes on logout",async()=>{
  vi.mocked(api.switchWorkspace).mockResolvedValue(undefined);vi.mocked(api.logout).mockResolvedValue(undefined);
  render(<AppShell session={session}><p>Protected content</p></AppShell>);
  fireEvent.change(screen.getByLabelText("Active workspace"),{target:{value:"org-b"}});
  await waitFor(()=>expect(api.switchWorkspace).toHaveBeenCalledWith("org-b"));
  fireEvent.click(screen.getByRole("button",{name:"Sign out"}));
  await waitFor(()=>expect(api.logout).toHaveBeenCalled());
  expect(replace).toHaveBeenCalledWith("/login");
});
