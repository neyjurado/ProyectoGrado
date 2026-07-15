# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

LigaDeportivaBarrial (LDP Conocoto) is a Spanish-language sports league management app: a FastAPI backend (`main.py`) backed by SQL Server, and a Vue 3 SPA frontend (`frontend-liga-vue/`). It manages equipos (teams), jugadores (players), árbitros (referees), partidos (matches/fixtures), suspensions, standings, and player match attendance/"camerino virtual" — plus image uploads to Firebase Storage.

## Commands

### Backend (FastAPI, from repo root)
```bash
.\venv\Scripts\activate          # activate the existing venv (Windows)
uvicorn main:app --reload        # run dev server at http://localhost:8000
```
- API docs: `http://localhost:8000/docs` (Swagger UI)
- Schema migrations are ad hoc: run `python ensure_schema.py` after pulling changes that add columns/tables — it idempotently adds missing tables/columns (see `ensure_schema.py` for the pattern used to extend the schema).
- No test suite or linter is configured for the backend.

### Frontend (Vue 3 + Vite, from `frontend-liga-vue/`)
```bash
npm install
npm run dev        # dev server, default http://localhost:5173
npm run build       # production build to dist/
npm run preview     # preview the production build
```
- No test suite or linter is configured for the frontend.

## Architecture

### Backend: single-file FastAPI app
All API routes, Pydantic models, and business-rule validators live in `main.py` — there is no router/module split. Key pieces:
- **`database.py`** — `get_db_connection()` opens a `pyodbc` connection to a local SQL Server instance using Windows Trusted Auth (server/database names are hardcoded, not env-driven).
- **`firebase_service.py`** — uploads images to Firebase Storage using `firebase-key.json` (a service-account credential file, gitignored, must exist locally) and returns a public URL. The frontend uploads files to `POST /upload-image` and then submits the returned URL as `url_foto` / `url_logo` fields in the entity create/update calls — Firebase upload and DB writes are separate requests, not atomic.
- **Every route** opens its own `pyodbc` connection, uses raw parameterized SQL (`cursor.execute(... , (?, ?))`), and closes the connection in a `finally` block. There's no ORM and no connection pooling layer beyond what `pyodbc`/SQL Server does itself.
- **Auth is minimal and un-hashed**: `/login` compares `password` to `Password_Hash` as plaintext (case-sensitive via `COLLATE SQL_Latin1_General_CP1_CS_AS`), and there's no session/token/JWT — the frontend just stores the returned user object in `localStorage`. Don't assume standard auth middleware exists; route protection (e.g. admin-only vs jugador-only) is enforced client-side by redirecting based on `rol`, not server-side.
- **Business-rule validators** are plain functions above the routes (`validar_password_segura`, `validar_fecha_nacimiento_max_100`, `validar_arbitros_distintos`, `validar_incidencias_vocalia`, etc.) — follow this pattern (a small validator returning an error string, or `''`/falsy when valid) rather than inlining validation logic into route bodies.
- **Suspension logic** (`calcular_si_esta_suspendido`) recomputes suspension status on the fly from match history (2 red-card-equivalent suspensions consumed sequentially, 5 accumulated yellows = 1 suspension) rather than storing a persistent "suspended" flag; `Suspensiones_Jugadores` is a separate manual-override table (admin can force-suspend for a year via `POST /jugadores/{id}/suspender`).
- **Fixture generation** (`POST /generar-calendario`) builds a round-robin schedule per categoría ("Primera", "Máxima") via `generar_round_robin_por_categoria`, and is password-gated by `FIXTURE_PASSWORD` (loaded from `FIXTURE_PASSWORD` env var, falling back to `fixture_password.txt`, falling back to a hardcoded default). `DELETE /partidos/fixture` (wipes the fixture) and `POST /config/fixture-password` share this same password gate. `limpiar_fixture()` cascades deletes across `Calificaciones_Arbitros`, `Asistencia`, `Estadisticas_Jugadores`, `Partidos` in that order (FK dependency order).
- **Standings/top-scorers** (`/estadisticas/posiciones/{categoria}`, `/goleadores/{categoria}`) are computed in Python by iterating finalized matches, not via SQL aggregation — team stats (pj/pg/pe/pp/gf/gc/gd/pts) are accumulated in a dict keyed by `Id_Equipo`.

### Frontend: flat Vue 3 SPA
- **Routing** (`src/router.js`) is a flat list with no route guards or lazy loading: `/` (Inicio), `/login`, `/admin` (AdminDashboard), `/jugador` (JugadorDashboard), `/registro-jugador` (Registro). `App.vue` is just a `<router-view>` shell — no persistent navbar/layout wrapper at the app root (`Navbar.vue` exists as a component used per-view where needed).
- **No API client / no `axios` / no `.env` usage in practice**: every view calls `fetch('http://127.0.0.1:8000/...')` directly with the backend URL hardcoded inline (despite `VUE_APP_API_URL` being defined in `.env.example` — it is not actually wired up anywhere in `src/`). When adding new API calls, match the existing pattern (hardcoded `http://127.0.0.1:8000` fetch calls) unless you're deliberately introducing a shared API client.
- **State is local + `localStorage`**, no Vuex/Pinia. Logged-in user (`{id, correo, rol, id_jugador}`) is stored under `localStorage['usuario']` by `Login.vue` and read back by views (e.g. `AdminDashboard.vue`) to gate behavior by `rol` ('Administrador' | 'Jugador').
- **`AdminDashboard.vue` is a large single-file "god view"** covering equipos, jugadores, árbitros, fixture generation, standings, suspensions, vocalía/match-closing (acta), and traspasos (transfers) all in one component with many local `ref`s — when editing it, locate the relevant section by its `cargarX`/handler function name rather than assuming separation of concerns.
- Styling uses Tailwind (`tailwind.config.js`, `postcss.config.js`) plus `src/style.css`.
- `@/` resolves to `frontend-liga-vue/src/` (see `vite.config.js`).

### Data model (inferred from SQL in `main.py`)
Core tables: `Equipos`, `Jugadores` (FK → `Equipos`), `Arbitros`, `Usuarios` (FK → `Jugadores`, holds `Rol`), `Partidos` (FK → `Equipos` x2 local/visitante, FK → `Arbitros` x3), `Estadisticas_Jugadores` (per-player per-match goals/cards), `Asistencia` (player match attendance), `Suspensiones_Jugadores`, `Calificaciones_Arbitros` (player ratings of referees). `Jugadores.Cedula` and `Arbitros.Cedula` are cross-checked against each other (a person can't be registered as both).

## Environment / secrets

- `firebase-key.json` (Firebase Admin SDK service account) must exist at repo root for uploads to work; it's gitignored and not committed.
- `FIXTURE_PASSWORD` env var overrides the fixture-management password; otherwise it's read from/written to `fixture_password.txt` at repo root (also gitignored-adjacent — check before committing).
- SQL Server connection details in `database.py` are hardcoded to a local named instance (`DESKTOP-A9DPDLM\SQLNEY`, database `LigaConocotoDB`) using Windows Trusted Auth — there's no `.env`-driven DB config despite `.env.example` existing.
