# Integracja: OCR App → Translator

Dokument do przekazania projektowi translatora. Opisuje zewnętrzne API OCR, które zwraca tekst z pozycjami na dokumencie.

---

## Kontekst

Osobny serwis **OCR App** (branch `mac`, Mac Studio) robi OCR na obrazach i PDF.  
Zwraca:
- pełny tekst (`text`)
- **pozycje każdego fragmentu tekstu** (`pages[].blocks[]`) — pod przyszłe składanie przetłumaczonego dokumentu

Translator ma:
1. Otrzymać plik (od użytkownika lub z OCR pipeline)
2. Albo wywołać OCR API, albo dostać już sparsowaną odpowiedź JSON
3. Przetłumaczyć tekst w blokach
4. (docelowo) złożyć dokument z przetłumaczonym tekstem w tych samych pozycjach

---

## Adres serwisu

| Środowisko | URL |
|------------|-----|
| **Linux VM owui01 (Docker, produkcja)** | z hosta: `http://localhost:8100` |
| **Z kontenera translatora (`alterai_default`)** | `http://ocr-backend:8000` |
| Mac Studio (native) | `http://localhost:8100` |
| Frontend testowy (Mac) | `http://localhost:3100` (tylko UI, nie API) |

### Produkcja (local-ai-translator na owui01)

OCR i translator muszą być w tej samej sieci Docker: **`alterai_default`**.

W konfiguracji translatora ustaw:

```
OCR_API_URL=http://ocr-backend:8000
```

Endpoint OCR: `POST http://ocr-backend:8000/api/ocr`

Deploy OCR: zobacz [DEPLOY-LINUX.md](DEPLOY-LINUX.md).

### Mac / lokalne testy

Port backendu: `.env.mac` → `BACKEND_PORT` (domyślnie **8100**).

Sprawdzenie czy działa:

```bash
# Linux / Docker (host port)
curl http://localhost:8100/api/health

# Mac native
curl http://localhost:8100/api/health
```

Odpowiedź:
```json
{"status":"ok","engines":["easyocr"]}
```
---

## Endpointy

### `GET /api/health`
Status serwisu.

### `GET /api/engines`
Lista silników. Na Macu zwykle tylko `easyocr`.

### `POST /api/ocr` — główny endpoint

**Request:** `multipart/form-data`

| Pole | Wymagane | Opis |
|------|----------|------|
| `file` | tak | Obraz lub PDF |
| `engine` | nie | Na Macu pomijaj — domyślnie `easyocr` |

**Obsługiwane formaty:** `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`, `.tif`, `.webp`, `.pdf`

**Przykład curl (z hosta owui01):**
```bash
curl -X POST http://localhost:8100/api/ocr \
  -F "file=@faktura.pdf"
```

**Przykład Python (z kontenera translatora):**
```python
import requests

# Production: Docker DNS name on alterai_default
url = "http://ocr-backend:8000/api/ocr"
# Local Mac tests: url = "http://localhost:8100/api/ocr"

with open("faktura.pdf", "rb") as f:
    response = requests.post(url, files={"file": f}, timeout=300)
response.raise_for_status()
ocr_result = response.json()
```

**Przykład JavaScript:**
```javascript
const formData = new FormData();
formData.append("file", fileInput.files[0]);

const response = await fetch("http://ocr-backend:8000/api/ocr", {
  method: "POST",
  body: formData,
});
const ocrResult = await response.json();
```
---

## Odpowiedź — pełny schemat

```json
{
  "filename": "faktura.pdf",
  "text": "--- Page 1 ---\nInvoice\nTotal: 100 PLN\n\n--- Page 2 ---\n...",
  "line_count": 24,
  "block_count": 18,
  "page_count": 2,
  "pages": [
    {
      "page": 1,
      "width": 1654,
      "height": 2339,
      "blocks": [
        {
          "text": "Invoice",
          "confidence": 0.9821,
          "bbox": [
            [120.5, 80.0],
            [210.0, 80.0],
            [210.0, 105.5],
            [120.5, 105.5]
          ],
          "box": {
            "x": 120.5,
            "y": 80.0,
            "width": 89.5,
            "height": 25.5
          }
        },
        {
          "text": "Total: 100 PLN",
          "confidence": 0.9543,
          "bbox": [[120.0, 200.0], [280.0, 200.0], [280.0, 220.0], [120.0, 220.0]],
          "box": { "x": 120.0, "y": 200.0, "width": 160.0, "height": 20.0 }
        }
      ]
    },
    {
      "page": 2,
      "width": 1654,
      "height": 2339,
      "blocks": []
    }
  ],
  "engine": "easyocr",
  "engine_name": "EasyOCR"
}
```

### Pola odpowiedzi

| Pole | Typ | Opis |
|------|-----|------|
| `filename` | string | Nazwa przesłanego pliku |
| `text` | string | Pełny tekst (wszystkie strony, bloki po `\n`, strony oddzielone `\n\n`, nagłówki `--- Page N ---`) |
| `line_count` | int | Liczba linii w `text` |
| `block_count` | int | Liczba bloków tekstu łącznie |
| `page_count` | int | Liczba stron |
| `pages` | array | **Kluczowe dla integracji** — dane per strona |
| `engine` | string | ID silnika (`easyocr`) |
| `engine_name` | string | Nazwa wyświetlana |

### Struktura `pages[]`

| Pole | Typ | Opis |
|------|-----|------|
| `page` | int | Numer strony (1-based) |
| `width` | int | Szerokość obrazu strony w pikselach |
| `height` | int | Wysokość obrazu strony w pikselach |
| `blocks` | array | Wykryte fragmenty tekstu |

### Struktura `blocks[]` — to ma dostać translator

| Pole | Typ | Opis |
|------|-----|------|
| `text` | string | **Tekst do przetłumaczenia** |
| `confidence` | float \| null | Pewność OCR (0–1), można filtrować niską jakość |
| `bbox` | `[[x,y], ...]` × 4 | Cztery rogi prostokąta w pikselach (układ współrzędnych: lewy górny róg = 0,0) |
| `box` | object | Uproszczony bbox: `x`, `y`, `width`, `height` w pikselach |

---

## Co translator powinien zrobić

### Minimalna integracja (tylko tekst)

Weź `ocr_result["text"]`, prześlij do tłumaczenia, zwróć przetłumaczony string.

### Integracja z layoutem (zalecana)

Dla każdej strony i bloku:

```python
for page in ocr_result["pages"]:
    page_num = page["page"]
    page_w = page["width"]
    page_h = page["height"]

    for block in page["blocks"]:
        original = block["text"]
        translated = translate(original)  # twój serwis

        # Zachowaj pozycję — pod przyszłe renderowanie PDF/obrazu
        output_block = {
            "page": page_num,
            "text": translated,
            "original_text": original,
            "box": block["box"],
            "bbox": block["bbox"],
            "confidence": block["confidence"],
        }
```

**Ważne:** tłumacz **blok po bloku** (`blocks[].text`), nie cały `text` naraz — inaczej stracisz mapowanie pozycji.

### Proponowany flow end-to-end

```
Użytkownik → plik (PDF/obraz)
    ↓
POST /api/ocr  (OCR App, port 8100)
    ↓
JSON z pages[].blocks[]
    ↓
Translator: tłumaczy blocks[].text
    ↓
(docelowo) Renderer: składa PDF/obraz z translated text w box/bbox
```

---

## Błędy API

| HTTP | Przyczyna |
|------|-----------|
| 400 | Zły format pliku, pusty plik, nieczytelny PDF |
| 500 | Błąd przetwarzania OCR |
| 503 | Brak włączonych silników |

Format błędu FastAPI:
```json
{"detail": "Unsupported file type '.docx'. Allowed: ..."}
```

---

## Uwagi techniczne

- **Pierwsze wywołanie** może trwać 1–2 min (pobieranie modelu EasyOCR).
- **PDF** jest renderowany do obrazów po 200 DPI (`PDF_RENDER_DPI`).
- Współrzędne `bbox`/`box` są w pikselach **wyrenderowanego obrazu strony**, nie punktach PDF.
- Język OCR: `OCR_LANG` w `.env.mac` (np. `en`, `pl`).
- OCR działa **natywnie na Macu** (bez Dockera), GPU Metal włączone (`OCR_USE_GPU=1`).

---

## Przykład: co wysłać do translatora (payload wejściowy)

Jeśli translator nie woła OCR sam, możesz przekazać mu gotowy JSON z pola `pages`:

```json
{
  "source": "ocr-app",
  "source_url": "http://localhost:8100/api/ocr",
  "filename": "faktura.pdf",
  "page_count": 1,
  "target_lang": "en",
  "pages": [
    {
      "page": 1,
      "width": 1654,
      "height": 2339,
      "blocks": [
        {
          "text": "Faktura VAT",
          "confidence": 0.97,
          "bbox": [[100, 50], [250, 50], [250, 80], [100, 80]],
          "box": { "x": 100, "y": 50, "width": 150, "height": 30 }
        }
      ]
    }
  ]
}
```

Translator powinien zwrócić analogiczną strukturę z `text` przetłumaczonym, **bez zmiany** `box`, `bbox`, `page`, `width`, `height`.

---

## Szybki test integracji

```bash
# 1. Health (host owui01)
curl http://localhost:8100/api/health

# 1b. Health z sieci Docker (jak translator)
docker run --rm --network alterai_default curlimages/curl:8.5.0 \
  http://ocr-backend:8000/api/health

# 2. OCR
curl -X POST http://localhost:8100/api/ocr \
  -F "file=@test.png" \
  -o ocr-result.json

# 3. Podgląd pierwszego bloku
cat ocr-result.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['pages'][0]['blocks'][0])"
```