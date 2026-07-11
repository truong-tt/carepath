export type Language = "vi" | "en";

const languageStorageKey = "carepath-demo-language";

export const copy = {
  vi: {
    title: "CarePath | Phiên dịch khám bệnh trực tiếp",
    breadcrumb: "Đường dẫn sản phẩm",
    status: "Bản mô phỏng tương tác",
    allProducts: "Tất cả chức năng",
    language: "Ngôn ngữ thanh sản phẩm",
    productName: "Phiên dịch khám bệnh trực tiếp",
  },
  en: {
    title: "CarePath | Medical Interpreter",
    breadcrumb: "Product breadcrumb",
    status: "Interactive mock simulation",
    allProducts: "All products",
    language: "Product bar language",
    productName: "Medical Interpreter",
  },
} as const;

export function initialLanguage(): Language {
  const value = new URLSearchParams(window.location.search).get("lang");
  if (value !== null) {
    return value === "en" || value === "vi" ? value : "vi";
  }
  return localStorage.getItem(languageStorageKey) === "en" ? "en" : "vi";
}

export function persistLanguage(language: Language) {
  localStorage.setItem(languageStorageKey, language);
}
