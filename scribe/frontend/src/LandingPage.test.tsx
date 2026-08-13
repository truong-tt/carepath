import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import LandingPage from "./LandingPage";

/**
 * The page is English by default now and Vietnamese behind the toggle, which
 * is the reverse of what these tests used to assert. The reason is in
 * docs/decisions/0023-foreign-patient-care-navigator.md: the first reader is a
 * foreign patient. Every Vietnamese assertion that used to run on mount still
 * runs — it runs after the toggle, because the Vietnamese half of this page has
 * to stay complete, not survive as a stub.
 */
function switchToVietnamese() {
  fireEvent.click(screen.getByRole("button", { name: "Chuyển sang tiếng Việt" }));
}

describe("LandingPage", () => {
  it("leads with the journey, in the patient's language", () => {
    render(<LandingPage />);

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Healthcare in Vietnam, without navigating it alone.",
      }),
    ).toBeInTheDocument();
    expect(document.documentElement.lang).toBe("en");
    // The documentation-burden calculator sold the use case the judges rejected.
    expect(screen.queryByRole("spinbutton", { name: /Số người bệnh/ })).not.toBeInTheDocument();
  });

  it("offers the patient's two doors, not a menu of tools", () => {
    render(<LandingPage />);

    const care = screen.getAllByRole("link", { name: "I need medical care" });
    expect(care.length).toBeGreaterThan(0);
    care.forEach((link) => expect(link).toHaveAttribute("href", "/get-care/"));

    // Someone already holding Vietnamese paper skips the first four steps.
    const paperwork = screen.getAllByRole("link", { name: "I already have a prescription" });
    expect(paperwork.length).toBeGreaterThan(0);
    paperwork.forEach((link) => expect(link).toHaveAttribute("href", "/dich-giay-to/"));
  });

  it("names all six steps of one journey", () => {
    render(<LandingPage />);

    // Scoped to the journey section: "Find care" is also a Try-it item, and an
    // unscoped query would pass on the wrong element.
    const journey = within(document.getElementById("journey")!);
    for (const step of ["Find care", "Prepare", "Visit", "Verify", "Paperwork", "Follow-up"]) {
      expect(journey.getByRole("heading", { name: step })).toBeInTheDocument();
    }
    expect(screen.getByText(/One product, not four tools/)).toBeInTheDocument();
  });

  it("puts one patient's clock next to the statistics", () => {
    render(<LandingPage />);

    expect(screen.getByRole("heading", { name: "Emma, a tourist in Hanoi." })).toBeInTheDocument();
    expect(screen.getByText(/She leaves holding a prescription written in Vietnamese/)).toBeInTheDocument();
    expect(
      screen.getByText("That is one problem, not four separate translation problems."),
    ).toBeInTheDocument();
  });

  it("does not market the clinician's tools as products of their own", () => {
    render(<LandingPage />);

    // They are still reachable — they are simply named as what they are: the
    // other person's door into the same journey.
    expect(screen.getByRole("link", { name: "For clinics: start a bilingual visit" })).toHaveAttribute(
      "href",
      "/kham-song-ngu/",
    );
  });

  it("states the harm evidence with its real figures", () => {
    render(<LandingPage />);

    expect(screen.getByText(/49.1%/)).toBeInTheDocument();
    expect(screen.getByText(/29.5%/)).toBeInTheDocument();
    expect(screen.getByText(/52.4% against 35.9%/)).toBeInTheDocument();
    expect(screen.getByText(/21.2 million/)).toBeInTheDocument();
    expect(screen.getByText(/161,992 foreign nationals/)).toBeInTheDocument();
  });

  it("credits the comparison to the study it comes from", () => {
    render(<LandingPage />);

    // The 29.5%/49.1% pair is the strongest claim on the page and it is not
    // ours. An uncredited figure is indistinguishable from an invented one.
    expect(screen.getByText(/Int J Qual Health Care 2007;19\(2\)/)).toBeInTheDocument();
  });

  it("does not price-compete on numbers that are not true", () => {
    render(<LandingPage />);

    expect(screen.queryByText(/25–100 USD/)).not.toBeInTheDocument();
    expect(screen.getByText(/does not replace an interpreter/)).toBeInTheDocument();
  });

  it("keeps the evidence inside its limits", () => {
    render(<LandingPage />);

    expect(screen.getByText(/not from CarePath/)).toBeInTheDocument();
    expect(screen.getByText("No clinical trial.")).toBeInTheDocument();
    expect(screen.getByText("No measurement on handwriting.")).toBeInTheDocument();
  });

  it("only claims measurements that were actually run", () => {
    render(<LandingPage />);

    // No rounding up: negation is 98% and is stated as 98% on its own row.
    expect(screen.getByRole("row", { name: /Negation\s+98%/ })).toBeInTheDocument();
    expect(screen.getByText(/not a clinical trial/)).toBeInTheDocument();
  });

  it("states the safety boundaries", () => {
    render(<LandingPage />);

    expect(screen.getByText("No diagnosis, no prescribing, no medical advice.")).toBeInTheDocument();
    expect(
      screen.getByText("No audio is stored. No document images are stored."),
    ).toBeInTheDocument();
  });

  it("shows the Vietnamese document with its English resolved beneath", () => {
    render(<LandingPage />);

    // The pivot's whole claim in one object: Vietnamese paper the patient
    // cannot read, English underneath, and two dose lines withheld.
    expect(screen.getByText("Không uống rượu trong thời gian dùng thuốc")).toBeInTheDocument();
    expect(screen.getByText("Do not drink alcohol while taking this medicine")).toBeInTheDocument();
    expect(screen.getAllByText("Withheld").length).toBe(2);
    expect(screen.getByText(/The clinician confirms every line/)).toBeInTheDocument();
  });

  it("keeps the Vietnamese page complete for the clinic that reads it", () => {
    render(<LandingPage />);
    switchToVietnamese();

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Khám chữa bệnh ở Việt Nam, không phải tự xoay xở một mình.",
      }),
    ).toBeInTheDocument();
    expect(document.documentElement.lang).toBe("vi");
    // Diacritics and the sourced figures survive the toggle in both directions.
    expect(screen.getByText(/49,1%/)).toBeInTheDocument();
    expect(screen.getByText(/21,2 triệu/)).toBeInTheDocument();
    expect(screen.getByText(/không thay thế phiên dịch viên/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Đối chiếu thuốc" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Lúc ra viện" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Khi ký cam kết" })).toBeInTheDocument();
  });

  it("lets a clinic say which function it wants a pilot of", () => {
    render(<LandingPage />);

    // The form follows the page's language rather than sitting in Vietnamese
    // inside an English section — a clinic reading the English page and filling
    // a Vietnamese form was the seam the pivot introduced.
    fireEvent.click(screen.getByText("Pilot CarePath at your clinic"));
    expect(screen.getByRole("combobox", { name: "Product interest" })).toBeInTheDocument();

    switchToVietnamese();
    expect(screen.getByRole("combobox", { name: "Chức năng quan tâm" })).toBeInTheDocument();
  });

  it("offers the journey and the document reader as separate ways in", () => {
    render(<LandingPage />);

    expect(screen.getByRole("link", { name: "Walk the journey" })).toHaveAttribute(
      "href",
      "/get-care/",
    );
    expect(screen.getByRole("link", { name: "Or read a real document instead" })).toHaveAttribute(
      "href",
      "/thu-nghiem/",
    );
  });

  it("names the three moments the harm evidence points at", () => {
    render(<LandingPage />);

    expect(screen.getByRole("heading", { name: "Medication reconciliation" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Discharge" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Informed consent" })).toBeInTheDocument();
    expect(screen.getByText(/All three of these happen after it/)).toBeInTheDocument();
  });
});
