# Techtivist API

Base URL: `https://d2ftw.westus2.cloudapp.azure.com`

## Auth

OAuth2 client credentials. Set in `.env`:

```
D2_CLIENT_ID=...
D2_CLIENT_SECRET=...
AZURE_STORAGE_CONNECTION_STRING=...
```

Token endpoint: `POST /o/token/` with `grant_type=client_credentials`. Tokens expire after 7 days.

See `test_api.py` to verify credentials are working.

---

## Endpoints

### `POST /o/token/`
Fetch a Bearer token.

### `GET /d2-api`
Main query endpoint. Returns paginated results.

Key query params:
| Param | Description |
|---|---|
| `targetentity` | Entity type to query. Use `provcase` to fetch provisional case fields directly. |
| `caseids` | Resource UUID of the case to fetch. |
| `provisional_case_resourceid` | Filter results by provisional case. |

**Fetching a provisional case:**
```python
requests.get("/d2-api", params={"targetentity": "provcase", "caseids": "<prov_case_uuid>"})
```

Each result includes:
- `extracted_death_classification` — `bool | None`. `None` means no tile was set (not the same as `False`).
- `extracted_case_numbers` — `list[str]`. Deduplicated, aggregated from page ranges, filename metadata, and filepath metadata across all linked documents.

### `GET /graph-summary`
Returns all graphs with their nodegroups and field definitions (name, datatype, required, exportable).

### `GET /case`
Single case details by resource ID. Currently returns 500 for some resource types.

### `GET /sheets-view`
Spreadsheet operations (GET, POST).

---

## Azure Blob Storage

Two containers accessed via `AZURE_STORAGE_CONNECTION_STRING`:

### `ocr` — `fetch_ocr.py` (`DocText`)
Returns paged OCR text for a document by SHA1.

```python
dt = DocText()
pages = dt.get_text(sha1)  # returns List[PageText]
# pages[i].page_number, pages[i].text
```

Blob path pattern: `sha1:<sha1>/`
Local cache: `DOCTEXT_CACHE_DIR` (default `/var/tmp/ayyub/clean_ocr_cache`)

### `case-files` — `download_pdf.py` (`DocPDF`)
Downloads a PDF by SHA1.

```python
dp = DocPDF()
path = dp.get_pdf(sha1)  # returns Path to cached PDF
```

Blob path pattern: `<sha1[:2]>/<sha1[2:4]>/<sha1[4:6]>/<sha1>`
Local cache: `DOCPDF_CACHE_DIR` (default `../data/output`)

---

## Scripts

### `test_api.py`
Verifies auth by hitting `/o/token/` and printing the response.

### `merge.py`
Enriches the merged case index (`20260212_case_index_output_all.jsonl`) with two fields fetched from provisional cases:
- `extracted_death_classifications` — list of non-null death classification booleans across all provisional cases for a row
- `extracted_case_numbers` — deduplicated case numbers across all provisional cases for a row

Controlled by a global flag at the top of the file:
```python
TEST = True   # picks a random case → writes to enriched_test.jsonl
TEST = False  # processes all cases → writes to enriched_full.jsonl
```

Uses `provisional_case_resourceids` from each row as the join key.
