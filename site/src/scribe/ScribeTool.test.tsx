import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import ScribeTool, { RichText } from "./ScribeTool";

const healthResponse = {
  ok: true,
  json: async () => ({
    asr_ready: true,
    llm_ready: true,
    asr_provider: "mock",
    llm_provider: "offline",
  }),
};

function soapResponse() {
  return {
    ok: true,
    text: async () =>
      JSON.stringify({
        soap: {
          subjective: "Đau đầu từ sáng nay.",
          objective: "- Huyết áp **160/90 mmHg**\n- Mạch 88",
          assessment: "Tăng huyết áp chưa kiểm soát.",
          plan: "Tái khám sau một tuần.",
          review_required: true,
          missing_information: ["Tiền sử dị ứng"],
        },
        metadata: { latency_ms: 3200 },
      }),
  };
}

function selectWav() {
  const input = document.querySelector('input[type="file"]') as HTMLInputElement;
  const file = new File(["RIFF"], "kham.wav", { type: "audio/wav" });
  fireEvent.change(input, { target: { files: [file] } });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("ScribeTool", () => {
  it("uploads audio and renders the SOAP draft with review banner", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(healthResponse)
      .mockResolvedValueOnce(soapResponse());
    vi.stubGlobal("fetch", fetchMock);

    render(<ScribeTool language="vi" />);
    await screen.findByText("Chế độ demo");
    expect(
      screen.getAllByRole("link", { name: "Tất cả sản phẩm" }),
    ).toHaveLength(2);
    expect(
      screen.getByText("Công cụ thí điểm · Cần bác sĩ duyệt"),
    ).toBeInTheDocument();

    const submit = screen.getByRole("button", { name: "Tạo bệnh án SOAP" });
    expect(submit).toBeDisabled();
    selectWav();
    expect(submit).toBeEnabled();
    fireEvent.click(submit);

    expect(await screen.findByText("Đau đầu từ sáng nay.")).toBeInTheDocument();
    expect(screen.getByText("160/90 mmHg")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Bản nháp do AI tạo, cần bác sĩ kiểm tra trước khi đưa vào hồ sơ bệnh án.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Tiền sử dị ứng")).toBeInTheDocument();

    const [, soapCall] = fetchMock.mock.calls;
    expect(soapCall[0]).toBe("/api/v1/soap-notes");
    expect(soapCall[1].method).toBe("POST");
  });

  it("shows the server's rate-limit message on 429", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(healthResponse)
        .mockResolvedValueOnce({
          ok: false,
          status: 429,
          text: async () =>
            JSON.stringify({
              detail: {
                message: "Bạn đã đạt giới hạn demo cho địa chỉ này.",
                retry_after_seconds: 60,
              },
            }),
        }),
    );

    render(<ScribeTool language="vi" />);
    selectWav();
    fireEvent.click(screen.getByRole("button", { name: "Tạo bệnh án SOAP" }));

    expect(
      await screen.findByText("Bạn đã đạt giới hạn demo cho địa chỉ này."),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Thử lại" }));
    expect(
      screen.getByRole("button", { name: "Tạo bệnh án SOAP" }),
    ).toBeInTheDocument();
  });

  it("marks the backend unreachable when health fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<ScribeTool language="en" />);
    expect(await screen.findByText("Server unreachable")).toBeInTheDocument();
  });
});

describe("RichText", () => {
  it("renders bullet runs as lists and honors bold", () => {
    render(<RichText text={"Mở đầu\n- Một **quan trọng**\n- Hai"} />);
    expect(screen.getByRole("list")).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    expect(screen.getByText("quan trọng").tagName).toBe("STRONG");
  });
});
