import logoUrl from "./assets/carepath-translate.svg";
import DemoPlayer from "./demo/DemoPlayer";

export default function App() {
  return (
    <main className="demo-page">
      <header className="demo-page__brand">
        <img src={logoUrl} alt="" />
        <div>
          <strong>CarePath Translate</strong>
          <span>Phiên dịch có bước xác nhận.</span>
        </div>
      </header>
      <DemoPlayer />
    </main>
  );
}
