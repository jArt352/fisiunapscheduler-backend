Plan import template and instructions

1. Template file (CSV)
- Path: `docs/plan_import_template.csv`
- Headers (first row): `code,name,credits,hours_theory,hours_practice,cycle`

2. How to use from the frontend
- Ask the user to select the target `Programa` (this maps to `School.id`).
- Ask for Plan metadata: `name`, `description` (optional), `start_year`, `end_year` (optional).
- Parse CSV and validate each row contains at least `code` and `name`.
- Map CSV columns to API fields:
  - `code` -> `code` (Course.code)
  - `name` -> `name` (Course.name)
  - `credits` -> `credits` (NOT stored by backend currently; included for reference)
  - `hours_theory` -> `hours_theory` (mapped to Course.theoretical_hours)
  - `hours_practice` -> `hours_practice` (mapped to Course.practical_hours)
  - `cycle` -> `cycle`

3. Example payload sent to POST `/api/plans/import/` (JSON)
```
{
  "name": "Plan 2020 Ingeniería de Sistemas",
  "description": "Importación masiva",
  "program": 1,
  "start_year": 2020,
  "end_year": null,
  "courses": [
    {"code":"131B10012","name":"CALCULO DIFERENCIAL","credits":4,"hours_theory":3,"hours_practice":2,"cycle":2},
    {"code":"131B10007","name":"INGLES BASICO II","credits":2,"hours_theory":1,"hours_practice":2,"cycle":2}
  ]
}
```
- Use `credentials: 'include'` when calling the endpoint if auth requires cookie.

4. Notes & caveats
- The backend currently does NOT persist `credits` (the `Course` model has no `credits` field). If you need it stored, request backend change.
- `Course.code` is unique: duplicate codes will cause errors for those rows and be reported back in the `errors` array of the response.
- The API response contains `created_courses` and `errors` arrays. Show both to the user.

5. Quick frontend checklist
- Provide a download link to `docs/plan_import_template.csv`.
- Allow user to select `Programa` from dropdown populated from backend.
- Validate CSV, show preview, then POST JSON to `/api/plans/import/`.

