import { useCallback, useEffect, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "";

const ACCEPTED_TYPES = [
  "image/png",
  "image/jpeg",
  "image/bmp",
  "image/tiff",
  "image/webp",
  "application/pdf",
];

const ACCEPTED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp", ".pdf"];

const FALLBACK_ENGINES = [
  { id: "paddle", name: "PaddleOCR", description: "Deep learning OCR" },
  { id: "tesseract", name: "Tesseract", description: "Classic OCR" },
  { id: "easyocr", name: "EasyOCR", description: "Deep learning OCR" },
];

function isAcceptedFile(file) {
  if (ACCEPTED_TYPES.includes(file.type)) return true;
  const name = file.name.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext));
}

function isPdf(file) {
  return file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
}

export default function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [status, setStatus] = useState("idle");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [engines, setEngines] = useState(FALLBACK_ENGINES);
  const [selectedEngine, setSelectedEngine] = useState("paddle");
  const inputRef = useRef(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/engines`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.engines?.length) {
          setEngines(data.engines);
          if (data.default) setSelectedEngine(data.default);
        }
      })
      .catch(() => {});
  }, []);

  const selectedEngineInfo = engines.find((e) => e.id === selectedEngine) ?? engines[0];

  const reset = useCallback(() => {
    setFile(null);
    setPreview(null);
    setStatus("idle");
    setResult(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  }, []);

  const processFile = useCallback(
    async (selectedFile) => {
      if (!isAcceptedFile(selectedFile)) {
        setError("Unsupported file type. Please upload an image or PDF.");
        setStatus("error");
        return;
      }

      setFile(selectedFile);
      setPreview(isPdf(selectedFile) ? null : URL.createObjectURL(selectedFile));
      setStatus("uploading");
      setError(null);
      setResult(null);

      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("engine", selectedEngine);

      try {
        const response = await fetch(`${API_BASE}/api/ocr`, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          throw new Error(body.detail || `Server error (${response.status})`);
        }

        const data = await response.json();
        setResult(data);
        setStatus("done");
      } catch (err) {
        setError(err.message || "OCR failed");
        setStatus("error");
      }
    },
    [selectedEngine]
  );

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDragOver(false);
      const dropped = e.dataTransfer.files[0];
      if (dropped) processFile(dropped);
    },
    [processFile]
  );

  const handleFileSelect = useCallback(
    (e) => {
      const selected = e.target.files[0];
      if (selected) processFile(selected);
    },
    [processFile]
  );

  const handleDownload = useCallback(() => {
    if (!result?.text) return;
    const baseName = (file?.name || "ocr-result").replace(/\.[^.]+$/, "");
    const blob = new Blob([result.text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${baseName}-ocr.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }, [result, file]);

  const canInteract = status === "idle" || status === "error";

  return (
    <div className="app">
      <header className="header">
        <h1>OCR App</h1>
        <p>Drop an image or PDF to extract text</p>
      </header>

      <main className="main">
        {canInteract && (
          <>
            <fieldset className="engine-picker">
              <legend className="engine-picker__legend">OCR engine</legend>
              <div className="engine-picker__options">
                {engines.map((engine) => (
                  <label
                    key={engine.id}
                    className={`engine-option ${selectedEngine === engine.id ? "engine-option--active" : ""}`}
                  >
                    <input
                      type="radio"
                      name="engine"
                      value={engine.id}
                      checked={selectedEngine === engine.id}
                      onChange={() => setSelectedEngine(engine.id)}
                    />
                    <span className="engine-option__name">{engine.name}</span>
                    <span className="engine-option__desc">{engine.description}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            <div
              className={`dropzone ${dragOver ? "dropzone--active" : ""}`}
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => inputRef.current?.click()}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
            >
              <div className="dropzone-icon">📄</div>
              <p className="dropzone-title">Drop your file here</p>
              <p className="dropzone-hint">Images or PDF — click to browse</p>
              <input
                ref={inputRef}
                type="file"
                accept={[...ACCEPTED_TYPES, ...ACCEPTED_EXTENSIONS].join(",")}
                onChange={handleFileSelect}
                hidden
              />
            </div>
          </>
        )}

        {status === "uploading" && (
          <div className="processing">
            {preview ? (
              <img src={preview} alt="Preview" className="preview" />
            ) : file && isPdf(file) ? (
              <div className="pdf-preview">📕 PDF document</div>
            ) : null}
            <div className="spinner" />
            <p>Processing with {selectedEngineInfo?.name ?? selectedEngine}…</p>
            <p className="filename">{file?.name}</p>
          </div>
        )}

        {status === "done" && result && (
          <div className="result">
            {preview ? (
              <img src={preview} alt="Preview" className="preview" />
            ) : file && isPdf(file) ? (
              <div className="pdf-preview">📕 PDF document</div>
            ) : null}
            <p className="filename">{file?.name}</p>
            <div className="result-meta">
              <span className="result-engine">{result.engine_name}</span>
              {" · "}
              {result.page_count > 1 && <span>{result.page_count} pages · </span>}
              {result.line_count} line{result.line_count !== 1 ? "s" : ""} detected
            </div>
            <pre className="result-text">{result.text || "(no text detected)"}</pre>
            <div className="actions">
              <button className="btn btn--download" onClick={handleDownload}>
                Download result
              </button>
              <button className="btn btn--new" onClick={reset}>
                New file
              </button>
            </div>
          </div>
        )}

        {status === "error" && (
          <div className="error-panel">
            <p className="error-message">{error}</p>
            <button className="btn btn--new" onClick={reset}>
              New file
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
