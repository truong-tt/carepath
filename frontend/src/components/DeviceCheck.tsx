import { useEffect, useRef, useState } from "react";

import { copy, type Language } from "../copy";
import { OnboardingFrame } from "./OnboardingFrame";

export type DeviceCheckResult = { deviceId?: string; voiceReady: boolean };

function MicIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" width="22" height="22" focusable="false">
      <rect x="9" y="3" width="6" height="11" rx="3" fill="none" stroke="currentColor" strokeWidth="1.8" />
      <path d="M6 11a6 6 0 0 0 12 0M12 17v4M9 21h6" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function DeviceCheck({ language = "vi", onComplete }: {
  language?: Language;
  onComplete: (result: DeviceCheckResult) => void;
}) {
  const text = copy[language].deviceCheck;
  const kicker = copy[language].productName;
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [deviceId, setDeviceId] = useState("");
  const [level, setLevel] = useState(0);
  const [state, setState] = useState<"idle" | "ready" | "unavailable" | "denied">("idle");
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const frameRef = useRef<number | null>(null);
  const testRef = useRef(0);

  function stopTest() {
    testRef.current += 1;
    if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
    frameRef.current = null;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    void audioContextRef.current?.close();
    audioContextRef.current = null;
  }

  useEffect(() => {
    void navigator.mediaDevices?.enumerateDevices?.().then((all) => {
      const microphones = all.filter((device) => device.kind === "audioinput");
      setDevices(microphones);
      setDeviceId((current) => current || microphones[0]?.deviceId || "");
      if (!microphones.length) setState("unavailable");
    }).catch(() => setState("unavailable"));
    return stopTest;
  }, []);

  async function testMicrophone() {
    stopTest();
    const attempt = ++testRef.current;
    if (!navigator.mediaDevices?.getUserMedia) {
      setState("unavailable");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: deviceId ? { deviceId: { exact: deviceId } } : true,
      });
      if (testRef.current !== attempt) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }
      streamRef.current = stream;
      const context = new AudioContext();
      audioContextRef.current = context;
      const analyser = context.createAnalyser();
      const source = context.createMediaStreamSource(stream);
      source.connect(analyser);
      const values = new Uint8Array(analyser.fftSize);
      const updateLevel = () => {
        analyser.getByteTimeDomainData(values);
        setLevel(values.reduce((sum, value) => sum + Math.abs(value - 128), 0) / values.length / 128);
        frameRef.current = requestAnimationFrame(updateLevel);
      };
      updateLevel();
      setState("ready");
    } catch {
      stopTest();
      setState(devices.length ? "denied" : "unavailable");
    }
  }

  const blocked = state === "unavailable" || state === "denied";

  return (
    <OnboardingFrame consentSubmitted kicker={kicker} language={language} title={text.title} titleId="device-check-title">
      <section className="device-check" aria-labelledby="device-check-title">
        <div className={`green-room green-room--${state}`}>
          <p className="green-room__intro">
            <span className="green-room__icon" aria-hidden="true"><MicIcon /></span>
            {text.body}
          </p>
          {devices.length > 1 ? (
            <label className="green-room__picker">
              {text.microphone}
              <select value={deviceId} onChange={(event) => setDeviceId(event.target.value)}>
                {devices.map((device, index) => <option key={device.deviceId} value={device.deviceId}>{device.label || `${text.microphone} ${index + 1}`}</option>)}
              </select>
            </label>
          ) : null}
          <div className="level-meter">
            <span className="meta">{text.level}</span>
            <meter min="0" max="1" value={level} />
            <div className="level-meter__scale" aria-hidden="true">
              <span>{text.scaleLow}</span>
              <span>{text.scaleHigh}</span>
            </div>
          </div>
          {state === "ready" ? <p className="green-room__state green-room__state--ready" role="status">{text.ready}</p> : null}
          {state === "idle" ? <p className="green-room__state green-room__state--idle">{text.idle}</p> : null}
          {blocked ? <p className="green-room__state green-room__state--blocked" role="alert">{state === "unavailable" ? text.unavailable : text.denied}</p> : null}
          <div className="green-room__actions">
            <button className="secondary-outline" type="button" onClick={() => void testMicrophone()}>{state === "idle" ? text.test : text.retry}</button>
            {state === "ready" ? (
              <button className="primary" type="button" onClick={() => { stopTest(); onComplete({ deviceId, voiceReady: true }); }}>{text.continueVoice}</button>
            ) : null}
          </div>
        </div>
        <button className="text-button" type="button" onClick={() => { stopTest(); onComplete({ voiceReady: false }); }}>{text.continueTyped}</button>
      </section>
    </OnboardingFrame>
  );
}
