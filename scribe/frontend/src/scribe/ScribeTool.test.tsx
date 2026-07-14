import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import ScribeTool, { classifyFailure, RichText } from "./ScribeTool";

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
        raw_transcript: "dau dau tu sang nay huyet ap mot sau muoi tren chin muoi",
        corrected_transcript: "Đau đầu từ sáng nay, huyết áp 160/90 mmHg.",
        retrieved_terms: ["amlodipin", "tăng huyết áp"],
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
  it("renders only one review notice, SOAP, and missing information", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(healthResponse)
      .mockResolvedValueOnce(soapResponse());
    vi.stubGlobal("fetch", fetchMock);

    render(<ScribeTool />);
    await screen.findByText("Chế độ demo");
    expect(
      screen.getAllByRole("link", { name: "Tất cả chức năng" }),
    ).toHaveLength(2);
    expect(
      screen.getByText("Công cụ thí điểm · Cần bác sĩ duyệt"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Ghi chép bệnh án AI — bản nháp" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Ba bước để tạo bản nháp")).toBeInTheDocument();
    expect(screen.getByText("Chọn tệp âm thanh buổi khám đã được phép sử dụng")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Xem ca khám mẫu trước" })).toHaveAttribute("href", "/#demo");
    expect(screen.queryByRole("button", { name: "Tiếp tục tạo bản nháp" })).not.toBeInTheDocument();

    const submit = screen.getByRole("button", { name: "Tạo bản nháp SOAP" });
    expect(submit).toBeDisabled();
    selectWav();
    expect(submit).toBeEnabled();
    fireEvent.click(submit);

    expect(await screen.findByText("Đau đầu từ sáng nay.")).toBeInTheDocument();
    expect(screen.getByText("160/90 mmHg")).toBeInTheDocument();
    expect(screen.getAllByText("Bản nháp SOAP — cần bác sĩ kiểm tra")).toHaveLength(1);
    expect(screen.getByText("Tiền sử dị ứng")).toBeInTheDocument();
    expect(screen.queryByText("Đối chiếu trước khi sử dụng")).not.toBeInTheDocument();
    expect(screen.queryByText("Bản phiên âm tự động")).not.toBeInTheDocument();
    expect(screen.queryByText("Bản phiên âm sau hiệu chỉnh")).not.toBeInTheDocument();
    expect(screen.queryByText("Thuật ngữ đã đối chiếu")).not.toBeInTheDocument();
    expect(screen.queryByText("dau dau tu sang nay huyet ap mot sau muoi tren chin muoi")).not.toBeInTheDocument();
    expect(screen.queryByText("Đau đầu từ sáng nay, huyết áp 160/90 mmHg.")).not.toBeInTheDocument();
    expect(screen.queryByText("amlodipin")).not.toBeInTheDocument();
    expect(screen.queryByText("tăng huyết áp")).not.toBeInTheDocument();
    const resultText = screen.getByLabelText("Bản nháp y khoa theo bốn mục SOAP").textContent ?? "";
    expect(resultText.indexOf("Bản nháp SOAP — cần bác sĩ kiểm tra")).toBeLessThan(resultText.indexOf("Đau đầu từ sáng nay."));
    expect(resultText.indexOf("Đau đầu từ sáng nay.")).toBeLessThan(resultText.indexOf("Tiền sử dị ứng"));

    const [, soapCall] = fetchMock.mock.calls;
    expect(soapCall[0]).toBe("/api/v1/soap-notes");
    expect(soapCall[1].method).toBe("POST");
  });

  it("shows a localized rate-limit message and keeps the selected file for a manual retry", async () => {
    const fetchMock = vi
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
        });
    vi.stubGlobal("fetch", fetchMock);

    render(<ScribeTool />);
    selectWav();
    fireEvent.click(screen.getByRole("button", { name: "Tạo bản nháp SOAP" }));

    expect(
      await screen.findByText("Bạn đã đạt giới hạn tạo bản nháp. Vui lòng thử lại sau."),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Thử lại" }));
    expect(
      screen.getByRole("button", { name: "Tạo bản nháp SOAP" }),
    ).toBeInTheDocument();
    expect(screen.getByText("kham.wav · 4 B")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("does not expose raw server detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(healthResponse)
        .mockResolvedValueOnce({
          ok: false,
          status: 502,
          text: async () => "LLM_API_KEY is required for production-provider",
        }),
    );

    render(<ScribeTool />);
    selectWav();
    fireEvent.click(screen.getByRole("button", { name: "Tạo bản nháp SOAP" }));

    expect(await screen.findByText("Chưa thể tạo bản nháp lúc này. Hãy thử lại sau.")).toBeInTheDocument();
    expect(screen.queryByText(/LLM_API_KEY/)).not.toBeInTheDocument();
  });

  it("shows a localized offline error when the draft request cannot connect", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(healthResponse)
        .mockRejectedValueOnce(new TypeError("Failed to fetch")),
    );

    render(<ScribeTool />);
    selectWav();
    fireEvent.click(screen.getByRole("button", { name: "Tạo bản nháp SOAP" }));

    expect(
      await screen.findByText("Không thể kết nối với máy chủ. Hãy kiểm tra kết nối rồi thử lại."),
    ).toBeInTheDocument();
  });

  it("marks the backend unreachable when health fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<ScribeTool />);
    expect(await screen.findByText("Mất kết nối máy chủ")).toBeInTheDocument();
  });
});

describe("classifyFailure", () => {
  it.each([
    [400, "Unsupported file type", "unsupported"],
    [400, "Audio file too large", "oversize"],
    [429, "anything", "rateLimit"],
    [503, "ASR failed", "asr"],
    [502, "LLM failed", "llm"],
    [500, "anything", "unknown"],
  ] as const)("classifies status %i as %s", (status, detail, expected) => {
    expect(classifyFailure(status, detail)).toBe(expected);
  });

  it("shows clear empty states for optional review fields", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(healthResponse)
        .mockResolvedValueOnce({
          ok: true,
          text: async () => JSON.stringify({
            raw_transcript: "",
            corrected_transcript: "",
            retrieved_terms: [],
            soap: {
              subjective: "",
              objective: "",
              assessment: "",
              plan: "",
              missing_information: [],
            },
          }),
        }),
    );

    render(<ScribeTool />);
    selectWav();
    fireEvent.click(screen.getByRole("button", { name: "Tạo bản nháp SOAP" }));

    expect(await screen.findAllByText("Không có nội dung phiên âm để hiển thị.")).toHaveLength(4);
    expect(screen.getByText("Không có thông tin còn thiếu được ghi nhận.")).toBeInTheDocument();
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
