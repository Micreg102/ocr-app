import { useCallback, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "";
const ENGINE = "easyocr";

const ACCEPTED_TYPES = [
  "image/png",
  "image/jpeg",
  "image/bmp",
  "image/tiff",
  "image/webp",
  "application/pdf",
];

const ACCEPTED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp", ".pdf"];

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
  const inputRef = useRef(null);

  const reset = useCallback(() => {
    if (preview) URL.revokeObjectURL(preview);
    setFile(null);
    setPreview(null);
    setStatus("idle");
    setResult(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  }, [preview]);

  const selectFile = useCallback(
    (selectedFile) => {
      if (!isAcceptedFile(selectedFile)) {
        setError("Nieobsługiwany typ pliku. Wyślij obraz lub PDF.");
        setStatus("error");
        return;
      }

      if (preview) URL.revokeObjectURL(preview);
      setFile(selectedFile);
      setPreview(isPdf(selectedFile) ? null : URL.createObjectURL(selectedFile));
      setStatus("ready");
      setError(null);
      setResult(null);
      if (inputRef.current) inputRef.current.value = "";
    },
    [preview]
  );

  const runAnalyze = useCallback(async () => {
    if (!file) return;

    setStatus("uploading");
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("engine", ENGINE);

    try {
      const response = await fetch(`${API_BASE}/api/ocr`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `Błąd serwera (${response.status})`);
      }

      const data = await response.json();
      setResult(data);
      setStatus("done");
    } catch (err) {
      setError(err.message || "OCR nie powiodło się");
      setStatus("error");
    }
  }, [file]);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDragOver(false);
      const dropped = e.dataTransfer.files[0];
      if (dropped) selectFile(dropped);
    },
    [selectFile]
  );

  const handleFileSelect = useCallback(
    (e) => {
      const selected = e.target.files[0];
      if (selected) selectFile(selected);
    },
    [selectFile]
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

  const handleDownloadJson = useCallback(() => {
    if (!result) return;
    const baseName = (file?.name || "ocr-result").replace(/\.[^.]+$/, "");
    const blob = new Blob([JSON.stringify(result, null, 2)], {
      type: "application/json;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${baseName}-ocr.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [result, file]);

  const isUploading = status === "uploading";
  const canAnalyze = Boolean(file) && !isUploading;

  return (
    <div className="app">
      <header className="header">
        <h1>OCR App</h1>
        <p>Wybierz plik, a potem kliknij Analizuj</p>
      </header>

      <main className="main">
        <div className="engine-badge">
          <span className="engine-badge__label">Silnik OCR</span>
          <span className="engine-badge__name">EasyOCR</span>
          <span className="engine-badge__desc">Rozpoznawanie tekstu z obrazów i PDF</span>
        </div>

        {!isUploading && (
          <div
            className={`dropzone ${dragOver ? "dropzone--active" : ""} ${file ? "dropzone--compact" : ""}`}
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
            <div className="dropzone-icon">{file ? "🔄" : "📄"}</div>
            <p className="dropzone-title">
              {file ? "Zmień plik" : "Upuść plik tutaj"}
            </p>
            <p className="dropzone-hint">
              {file ? file.name : "Obraz lub PDF — kliknij, aby wybrać"}
            </p>
            <input
              ref={inputRef}
              type="file"
              accept={[...ACCEPTED_TYPES, ...ACCEPTED_EXTENSIONS].join(",")}
              onChange={handleFileSelect}
              hidden
            />
          </div>
        )}

        {file && preview && !isUploading && (
          <img src={preview} alt="Podgląd" className="preview" />
        )}

        {file && isPdf(file) && !isUploading && (
          <div className="pdf-preview">📕 Dokument PDF</div>
        )}

        {isUploading && (
          <div className="processing">
            {preview ? (
              <img src={preview} alt="Podgląd" className="preview" />
            ) : file && isPdf(file) ? (
              <div className="pdf-preview">📕 Dokument PDF</div>
            ) : null}
            <div className="spinner" />
            <p>Analizuję plik EasyOCR…</p>
            <p className="filename">{file?.name}</p>
          </div>
        )}

        {status === "done" && result && (
          <div className="result">
            <div className="result-meta">
              <span className="result-engine">{result.engine_name}</span>
              {" · "}
              {result.page_count > 1 && <span>{result.page_count} stron · </span>}
              {result.block_count ?? 0} {result.block_count === 1 ? "blok" : "bloków"}
              {" · "}
              {result.line_count} {result.line_count === 1 ? "linia" : "linii"}
            </div>
            <pre className="result-text">{result.text || "(nie wykryto tekstu)"}</pre>
            {result.pages?.length > 0 && (
              <details className="positions-panel">
                <summary>Pozycje tekstu ({result.block_count ?? 0} bloków)</summary>
                <pre className="positions-json">
                  {JSON.stringify(result.pages, null, 2)}
                </pre>
              </details>
            )}
            <div className="actions">
              <button className="btn btn--download" onClick={handleDownload}>
                Pobierz tekst
              </button>
              <button className="btn btn--json" onClick={handleDownloadJson}>
                Pobierz JSON
              </button>
              <button className="btn btn--new" onClick={reset}>
                Nowy plik
              </button>
            </div>
          </div>
        )}

        {status === "error" && (
          <div className="error-panel">
            <p className="error-message">{error}</p>
          </div>
        )}

        <div className="analyze-bar">
          <button
            className="btn btn--analyze"
            onClick={runAnalyze}
            disabled={!canAnalyze}
          >
            Analizuj
          </button>
        </div>
      </main>
    </div>
  );
}
