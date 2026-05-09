# Implementation Plan: Educational Quality Survey Recognition App

## 1. Current State Assessment

### Existing Assets (Preserve)

| Module | Purpose | Maturity |
|---|---|---|
| `image_aligner.py` | Fiducial marker detection + perspective warp | Proven |
| `checkbox_reader.py` | 14x3 grid density reading, RTL mapping | Proven |
| `vision_processor.py` | Orchestrates load -> align -> decode | Functional |
| `analytics_engine.py` | Form/batch scoring, report generation | Functional |
| `plotly_generator.py` | Stacked bar, pie, score HTML charts | Functional |
| `i18n.py` | en / fa / ps translation manager | Functional |
| `settings_page.py` | Card-based CustomTkinter settings UI | Reusable |

### Critical Gaps vs Specification

| Requirement | Current State | Severity |
|---|---|---|
| Persistent storage (SQLite) | In-memory DataFrame only | High |
| Survey entity (CRUD + status) | None | High |
| Multi-page GUI (Dashboard, Create, Process, Results) | Single page | High |
| PDF form generation | None | High |
| University branding + logo | None | Medium |
| Configurable question text (1-14) | Hardcoded | Medium |
| Manual correction UI | None | Medium |
| Per-image confidence | ok/failed binary only | Medium |
| Data export (CSV / PDF) | HTML report only | Medium |
| Raw data view | None | Low |
| Trend analysis | None | Low |

---

## 2. Strategic Decision: Stack

**Recommendation: Extend the Python / CustomTkinter codebase.**

Rationale:
- The OpenCV OMR pipeline is tuned to a real-world Persian form with hard-won margin and offset constants. Porting to JS / WebAssembly or a Python-backend / web-frontend architecture is high-risk and multi-week work.
- CustomTkinter can deliver all GUI pages in the spec (dashboard tables, cards, wizards, image preview) without a full rewrite.
- PDF generation can use `pikepdf` / `reportlab` (Python equivalents to `pdf-lib`).
- If a web-based UI is required later, the Python backend can be exposed via a local HTTP API and a thin client can connect to it. This is Phase 6.

---

## 3. Phased Implementation Plan

### Phase 0 - Foundation & Tooling (1-2 days)

**Goals:** Add dependencies, set up SQLite schema, establish migration discipline.

- [ ] Add to `requirements.txt`:
  - `sqlalchemy>=2.0` for ORM-like persistence
  - `pikepdf>=8.0` or `reportlab>=4.0` for PDF manipulation
  - `qrcode>=7.0` for survey ID embedding
  - `Pillow>=10.0` for logo resizing
- [ ] Create `src/persistence.py` with tables:
  - `Survey`: id, university, faculty, department, subject, professor, semester, academic_year, status (Draft/Processed/Analyzed), created_at, updated_at
  - `FormResult`: id, survey_id, form_id, q1..q14, form_score, valid, confidence, manually_corrected, image_path
  - `AppSettings`: key, value JSON blob (university name, logo path, question texts, coordinate map)
- [ ] Create `src/models.py` - dataclasses mirroring DB tables for clean layer passing.
- [ ] Write `tests/test_persistence.py` - round-trip CRUD for surveys and results.
- [ ] Update `Config` to load defaults from `AppSettings` on startup, falling back to current class constants.

### Phase 1 - Survey Metadata & Dashboard (2-3 days)

**Goals:** Replace the single-page flow with a survey-centric dashboard and CRUD.

- [ ] Restructure `gui.py` into a page-router pattern:
  - `DashboardPage` - survey list table
  - `SurveyFormPage` - create/edit survey metadata
  - `ProcessPage` - per-survey image upload + OMR run
  - `ResultsPage` - aggregated charts + tables
  - `SettingsPage` - existing page extended
- [ ] `DashboardPage` features:
  - `+ New Survey` button routes to `SurveyFormPage`
  - Sortable table: Subject, Professor, Semester, Academic Year, Status
  - Status icons: yellow Draft / blue Processed / green Analyzed
  - Row actions: Edit (Draft only), Process (Draft), Results (Processed/Analyzed), Delete (confirm dialog)
  - Search bar filters across Subject and Professor
  - Filter dropdown by Department
- [ ] `SurveyFormPage`:
  - Fields: University (read-only from settings), Faculty, Department, Subject, Professor Name, Semester (1-10), Academic Year
  - Save Survey inserts/updates SQLite, status = Draft, returns to Dashboard
  - Print Survey Form button calls PDFGenerator (Phase 2)
  - Context-aware: loads existing data when Edit is clicked
- [ ] Update `i18n.py` with new keys: new_survey, edit_survey, process, results, delete, confirm_delete, draft, processed, analyzed.

### Phase 2 - PDF Form Generation (2 days)

**Goals:** Produce prefilled survey PDFs with branding and metadata.

- [ ] Create `src/pdf_generator.py`:
  - `generate_prefilled_form(survey, output_path)`
  - Loads base template PDF from `assets/survey_template.pdf` (bundled) or configurable path
  - Embeds university logo image at configured (x, y) coordinate
  - Overlays university name text at configured coordinate
  - Overlays metadata fields (Faculty, Department, Subject, Professor, Semester, Academic Year) at their coordinate slots
  - Embeds QR code containing survey.id at designated spot
  - All coordinates stored in AppSettings under `pdf_coords` JSON key
- [ ] Add Print Survey Form button to `SurveyFormPage` that generates a temp PDF and opens it via `os.startfile` or `webbrowser`.
- [ ] Add `tests/test_pdf_generator.py` - verify output file is created and readable.

### Phase 3 - App Settings: Branding & Questions (1-2 days)

**Goals:** Make university name, logo, and question text configurable.

- [ ] Extend `SettingsFrame` with new cards:
  - **University Branding card:** University Name text entry; Logo Upload file picker (png/jpg) storing path in AppSettings with preview thumbnail.
  - **PDF Template Coordinates card:** Editable coordinate pairs for each metadata field and logo (simple JSON text area for v1, per-field rows in v1.1).
  - **Survey Questions card:** Table of 14 rows: Question # (read-only), Question Text (editable, RTL-friendly). Default values pre-filled with standard Persian questions. Save writes to AppSettings as JSON array.
- [ ] Update `Config` to read `QUESTION_TEXTS` list from AppSettings on startup.
- [ ] Update `AnalyticsEngine` and `PlotlyGenerator` to accept question texts and use them as labels instead of Q1, Q2, etc.

### Phase 4 - Per-Survey OMR Processing + Confidence (2-3 days)

**Goals:** Scope processing to a single survey, add confidence metrics, and a live thumbnail grid.

- [ ] `ProcessPage` layout:
  - Top: read-only metadata card showing the survey being processed.
  - Upload area: drag-and-drop or multi-file picker (JPG, PNG, TIFF).
  - Thumbnail grid of uploaded images with status badges: Queued / Processing / Success / Warning / Error.
  - Start Scanning button (enabled when at least 1 image is queued).
  - Live progress label: Scanning image 5 of 20.
- [ ] Extend `VisionProcessor` to return per-question confidence:
  - `process_form` returns density values per cell and a row-level confidence score.
  - A form is flagged Warning if any row has density near threshold or multiple selections.
- [ ] Store results in `FormResult` table scoped to `survey_id` instead of global `DataStore`.
- [ ] After scanning completes, update `Survey.status` to `Processed`.
- [ ] Add `tests/test_vision_confidence.py` - verify confidence scoring logic.

### Phase 5 - Results Visualization & Export (2 days)

**Goals:** Display aggregated results using configured question text and add exports.

- [ ] `ResultsPage` layout:
  - Survey Meta Summary Card: Subject, Professor, Semester, Academic Year, Number of Processed Forms.
  - Interactive charts: for each question 1-14, show distribution across Yes / No / Somewhat using question text from settings as titles.
  - Summary table: Question Number, Question Text, Count Yes, Count No, Count Somewhat, Total Responses, optional % Distribution.
  - Toggle View: switch between aggregated summary and Raw Data View (per-sheet responses, anonymized).
  - Revisit Forms link: opens ProcessPage in read-only mode for auditing.
- [ ] Export buttons:
  - Export as CSV: columns QuestionNumber, QuestionText, Count_Bli, Count_Kheir, Count_Nesbatan, TotalResponses.
  - Export as PDF: printable report with summary card, charts, and tables using full Question Text.
- [ ] On first view, automatically update `Survey.status` to `Analyzed`.
- [ ] Trend Analysis (basic): option to compare current survey results against previous surveys for the same Subject+Professor combination across different Semesters/Years.

### Phase 6 - Optional: Web-based Frontend (Future)

**Goals:** If a web-based UI is required, wrap the Python backend in a local HTTP API.

- [ ] Create `src/api.py` - FastAPI or Flask exposing endpoints:
  - GET /surveys, POST /surveys, PUT /surveys/{id}, DELETE /surveys/{id}
  - POST /surveys/{id}/process (accepts multipart image uploads)
  - GET /surveys/{id}/results
  - GET /settings, PUT /settings
  - POST /surveys/{id}/export?format=csv|pdf
- [ ] A web or desktop thin client connects to the localhost API.
- [ ] OMR pipeline remains untouched in Python.

---

## 4. Testing Strategy

- **Unit tests** for each new module before integration (`test_persistence.py`, `test_pdf_generator.py`, `test_models.py`).
- **Integration tests** for the full survey lifecycle: create -> print PDF -> process images -> view results -> export CSV.
- **GUI tests** using existing `test_gui.py` pattern (instantiate pages, verify widgets, simulate button clicks).
- **Regression tests** for OMR accuracy: run existing `test_checkbox_reader.py` and `test_image_aligner.py` after every change to ensure no vision pipeline regression.

---

## 5. File Structure After Implementation

```
OMR/
  main.py
  requirements.txt
  assets/
    survey_template.pdf
    report.html
  src/
    config.py
    models.py
    persistence.py
    gui.py                 (page router + all pages)
    settings_page.py       (extended)
    vision_processor.py    (extended for confidence)
    checkbox_reader.py     (extended for density export)
    image_aligner.py       (unchanged)
    analytics_engine.py    (extended for question text)
    plotly_generator.py    (extended for exports)
    pdf_generator.py       (new)
    i18n.py                (extended)
  tests/
    test_persistence.py
    test_pdf_generator.py
    test_models.py
    test_gui.py
    test_analytics.py
    test_checkbox_reader.py
    test_image_aligner.py
    test_vision_processor.py
```

---

## 6. Estimated Timeline

| Phase | Duration | Deliverable |
|---|---|---|
| Phase 0 | 1-2 days | SQLite schema, models, tests |
| Phase 1 | 2-3 days | Dashboard + Survey CRUD |
| Phase 2 | 2 days | PDF form generation |
| Phase 3 | 1-2 days | Branding + question config |
| Phase 4 | 2-3 days | Per-survey OMR + confidence |
| Phase 5 | 2 days | Results + CSV/PDF export |
| **Total v1.0** | **10-14 days** | All core spec features |
| Phase 6 | 3-5 days | Web-based thin client (optional) |
