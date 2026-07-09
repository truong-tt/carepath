import logoUrl from "./assets/carepath-translate.svg";

export default function App() {
  return (
    <main className="brand-intro">
      <div className="brand-intro__mark" aria-hidden="true">
        <img src={logoUrl} alt="" />
      </div>
      <p className="brand-intro__parent">CarePath</p>
      <h1>Translate</h1>
      <p>Phiên dịch có bước xác nhận.</p>
      <p className="brand-intro__note">
        Bản mô phỏng — không phải bản dịch trực tiếp
      </p>
    </main>
  );
}
