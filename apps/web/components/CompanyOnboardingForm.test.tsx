import {fireEvent,render,screen,waitFor} from "@testing-library/react";
import {expect,it,vi} from "vitest";
import {CompanyOnboardingForm} from "./CompanyOnboardingForm";
import {completeCompanyOnboarding} from "@/lib/api";

vi.mock("next/navigation",()=>({useRouter:()=>({refresh:vi.fn()})}));
vi.mock("@/lib/api",()=>({completeCompanyOnboarding:vi.fn()}));

it("completes an authenticated incomplete organization workspace",async()=>{
  vi.mocked(completeCompanyOnboarding).mockResolvedValue({} as never);
  render(<CompanyOnboardingForm organizationName="Incomplete Org"/>);
  fireEvent.change(screen.getByLabelText("Description"),{target:{value:"A complete description"}});
  fireEvent.change(screen.getByLabelText("Services"),{target:{value:"Data, Cloud"}});
  fireEvent.submit(screen.getByRole("button",{name:"Finish setup"}).closest("form")!);
  await waitFor(()=>expect(completeCompanyOnboarding).toHaveBeenCalled());
  expect(vi.mocked(completeCompanyOnboarding).mock.calls[0][0].service_categories).toEqual(["Data","Cloud"]);
});
