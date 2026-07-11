import { useEffect, useRef, useState } from "react";

import { copy, type Language } from "../copy";

export type DeviceCheckResult = { deviceId?: string; voiceReady: boolean };

export function DeviceCheck({ language = "vi", onComplete }: {
  language?: Language;
  onComplete: (result: DeviceCheckResult) => void;
}) {
  const text = copy[language].deviceCheck;
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

  return (
    <main className="page" lang={language}>
      <section className="device-check" aria-labelledby="device-check-title">
        <h1 id="device-check-title">{text.title}</h1>
        <p>{text.body}</p>
        {devices.length > 1 ? (
          <label>
            {text.microphone}
            <select value={deviceId} onChange={(event) => setDeviceId(event.target.value)}>
              {devices.map((device, index) => <option key={device.deviceId} value={device.deviceId}>{device.label || `${text.microphone} ${index + 1}`}</option>)}
            </select>
          </label>
        ) : null}
        <button type="button" onClick={() => void testMicrophone()}>{state === "idle" ? text.test : text.retry}</button>
        {state === "ready" ? (
          <>
            <p role="status">{text.ready}</p>
            <label>{text.level}<meter min="0" max="1" value={level} /></label>
            <button type="button" onClick={() => { stopTest(); onComplete({ deviceId, voiceReady: true }); }}>{text.continueVoice}</button>
          </>
        ) : null}
        {state === "unavailable" || state === "denied" ? <p role="alert">{state === "unavailable" ? text.unavailable : text.denied}</p> : null}
        <button className="text-button" type="button" onClick={() => { stopTest(); onComplete({ voiceReady: false }); }}>{text.continueTyped}</button>
      </section>
    </main>
  );
}
