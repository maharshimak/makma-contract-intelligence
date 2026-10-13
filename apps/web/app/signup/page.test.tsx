import {fireEvent,render,screen,waitFor} from "@testing-library/react";
import {beforeEach,describe,expect,it,vi} from "vitest";
import Signup from "./page";
import {api} from "@/lib/api";

const replace=vi.fn();
vi.mock("next/navigation",()=>({useRouter:()=>({replace,refresh:vi.fn()})}));
vi.mock("@/lib/api",()=>({api:{signup:vi.fn()}}));

describe("Signup",()=>{
  beforeEach(()=>{vi.clearAllMocks()});
  it("separates professional signup from company authority",async()=>{
    vi.mocked(api.signup).mockResolvedValue({account_type:"PROFESSIONAL"});
    render(<Signup/>);
    fireEvent.click(screen.getByRole("button",{name:"Professional"}));
    expect(screen.queryByLabelText("Company name")).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Your name"),{target:{value:"Pilot Professional"}});
    fireEvent.change(screen.getByLabelText("Email"),{target:{value:"pilot@example.com"}});
    fireEvent.change(screen.getByLabelText("Password"),{target:{value:"Professional1234"}});
    fireEvent.submit(screen.getByRole("button",{name:"Create account"}).closest("form")!);
    await waitFor(()=>expect(api.signup).toHaveBeenCalledWith({account_type:"PROFESSIONAL",email:"pilot@example.com",password:"Professional1234",display_name:"Pilot Professional"}));
    expect(replace).toHaveBeenCalledWith("/professional");
  });
});
