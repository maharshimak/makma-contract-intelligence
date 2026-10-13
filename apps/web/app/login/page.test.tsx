import {fireEvent,render,screen,waitFor} from "@testing-library/react";
import {beforeEach,describe,expect,it,vi} from "vitest";
import Login from "./page";
import {api} from "@/lib/api";

const replace=vi.fn();
vi.mock("next/navigation",()=>({useRouter:()=>({replace,refresh:vi.fn()}),useSearchParams:()=>new URLSearchParams("next=/professional")}));
vi.mock("@/lib/api",()=>({api:{login:vi.fn(),demoLogin:vi.fn()}}));

describe("Login",()=>{
  beforeEach(()=>vi.clearAllMocks());
  it("submits credentials and returns to the requested protected route",async()=>{
    vi.mocked(api.login).mockResolvedValue(undefined);
    render(<Login/>);
    fireEvent.change(screen.getByLabelText("Email"),{target:{value:"pilot@example.com"}});
    fireEvent.change(screen.getByLabelText("Password"),{target:{value:"PilotPassword123"}});
    fireEvent.submit(screen.getByRole("button",{name:"Sign in"}).closest("form")!);
    await waitFor(()=>expect(api.login).toHaveBeenCalledWith("pilot@example.com","PilotPassword123"));
    expect(replace).toHaveBeenCalledWith("/professional");
  });
});
