import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import LeadForm from "./LeadForm";
import { scenarios } from "./demo/scenarios";

function fillRequiredFields() {
  fireEvent.change(screen.getByRole("textbox", { name: "Họ và tên" }), {
    target: { value: "Nguyễn Minh Anh" },
  });
  fireEvent.change(screen.getByRole("textbox", { name: "Vai trò" }), {
    target: { value: "Giám đốc phòng khám" },
  });
  fireEvent.change(screen.getByRole("textbox", { name: "Email hoặc Zalo" }), {
    target: { value: "minhanh@example.com" },
  });
}

describe("LeadForm", () => {
  it("posts the configured payload to the lead endpoint", async () => {
    const fetcher = vi.fn(async () => new Response(null, { status: 204 })) as unknown as typeof fetch;
    render(
      <LeadForm
        clinic="Phòng khám Minh Tâm"
        endpoint="https://leads.example.test/pilot"
        fetcher={fetcher}
        language="vi"
        scenario={scenarios[0]}
        specialty="Nội tổng quát"
        transcript="VI: Uống nửa viên.\nEN: Take half a tablet."
      />,
    );

    fillRequiredFields();
    fireEvent.click(
      screen.getByRole("button", { name: "Chuẩn bị yêu cầu thí điểm" }),
    );

    await waitFor(() =>
      expect(screen.getByText("Đã gửi yêu cầu thí điểm.")).toBeInTheDocument(),
    );
    expect(fetcher).toHaveBeenCalledOnce();
    const [, request] = (fetcher as ReturnType<typeof vi.fn>).mock.calls[0];
    const payload = JSON.parse(String(request.body));
    expect(payload.interest).toBe("both");
    expect(payload.scenarioId).toBe("prescription");
    expect(payload.transcript).toContain("Take half a tablet");
  });

  it("opens a prefilled mail draft when no endpoint is configured", async () => {
    const onMailto = vi.fn();
    render(
      <LeadForm
        clinic="Phòng khám Minh Tâm"
        endpoint=""
        leadEmail="pilot@example.com"
        language="vi"
        onMailto={onMailto}
        scenario={scenarios[1]}
        specialty="Dị ứng"
        transcript="VI: Không dị ứng.\nEN: Not allergic."
      />,
    );

    fillRequiredFields();
    fireEvent.click(
      screen.getByRole("button", { name: "Chuẩn bị yêu cầu thí điểm" }),
    );

    await waitFor(() => expect(onMailto).toHaveBeenCalledOnce());
    const mailto = decodeURIComponent(onMailto.mock.calls[0][0]);
    expect(mailto).toContain("mailto:pilot@example.com");
    expect(mailto).toContain("Kiểm tra dị ứng — xác nhận phủ định");
    expect(mailto).toContain("Not allergic");
    expect(
      screen.getByText(
        "Đã mở bản nháp email. Hãy kiểm tra và gửi thư để hoàn tất.",
      ),
    ).toBeInTheDocument();
  });

  it("shows inline errors without attempting submission", () => {
    const fetcher = vi.fn();
    render(
      <LeadForm
        clinic="Phòng khám Minh Tâm"
        endpoint="https://leads.example.test/pilot"
        fetcher={fetcher as unknown as typeof fetch}
        language="vi"
        scenario={scenarios[0]}
        specialty="Nội tổng quát"
        transcript=""
      />,
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Chuẩn bị yêu cầu thí điểm" }),
    );

    expect(screen.getAllByText("Vui lòng điền trường này.")).toHaveLength(3);
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("submits a selectable Scribe interest without interpreter context", async () => {
    const fetcher = vi.fn(async () => new Response(null, { status: 204 })) as unknown as typeof fetch;
    render(
      <LeadForm
        clinic="Phòng khám Minh Tâm"
        endpoint="https://leads.example.test/pilot"
        fetcher={fetcher}
        language="vi"
        scenario={scenarios[0]}
        specialty="Nội tổng quát"
        transcript="VI: Uống nửa viên.\nEN: Take half a tablet."
      />,
    );

    fireEvent.change(screen.getByRole("combobox", { name: "Sản phẩm quan tâm" }), {
      target: { value: "scribe" },
    });
    fillRequiredFields();
    fireEvent.click(
      screen.getByRole("button", { name: "Chuẩn bị yêu cầu thí điểm" }),
    );

    await waitFor(() => expect(fetcher).toHaveBeenCalledOnce());
    const [, request] = (fetcher as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(JSON.parse(String(request.body))).toMatchObject({
      interest: "scribe",
      scenarioId: "",
      scenarioTitle: "",
      transcript: "",
    });
  });

  it("reports controlled product-interest changes", () => {
    const onInterestChange = vi.fn();
    render(
      <LeadForm
        clinic="Phòng khám Minh Tâm"
        interest="interpreter"
        language="vi"
        onInterestChange={onInterestChange}
        scenario={scenarios[0]}
        specialty="Nội tổng quát"
        transcript=""
      />,
    );

    const selector = screen.getByRole("combobox", { name: "Sản phẩm quan tâm" });
    expect(selector).toHaveValue("interpreter");
    fireEvent.change(selector, { target: { value: "both" } });
    expect(onInterestChange).toHaveBeenCalledWith("both");
  });
});
