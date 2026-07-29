# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) and AI assistants when working with code in this repository.

## Project overview

LigaDeportivaBarrial (LDP Conocoto) is a Spanish-language sports league management web app for local soccer leagues:
- **Backend:** FastAPI (`main.py`) backed by Microsoft SQL Server (`LigaConocotoDB`) via `pyodbc` and Firebase Storage (`firebase_service.py`).
- **Frontend:** Vue 3 SPA (`frontend-liga-vue/`) built with Vite, Tailwind CSS, and Vue Router.

It manages equipos (teams), jugadores (players), árbitros (referees), partidos (matches/fixtures), suspensions, standings, match statistics, vocalías (match sheets), and a player portal ("camerino virtual").

## Commands

### Backend (FastAPI, from repo root)
```bash
.\venv\Scripts\activate          # activate the existing venv (Windows)
uvicorn main:app --reload        # run dev server at http://127.0.0.1:8000
```
- API docs: `http://127.0.0.1:8000/docs` (Swagger UI)
- Schema migrations: run `python ensure_schema.py` idempotently after adding columns/tables to SQL Server.

### Frontend (Vue 3 + Vite, from `frontend-liga-vue/`)
```bash
npm install
npm run dev         # dev server, default http://localhost:5173
npm run build       # production build to dist/
npm run preview     # preview the production build
```

---

## Architecture & Recent Enhancements

### 1. Normalización y Sanitización de Nombres de Equipos (Regex)
- **Backend (`main.py`):** `normalizar_nombre_equipo(nombre: str) -> str` colapsa múltiples espacios intermedios mediante `re.sub(r'\s+', ' ', nombre.strip()).upper()`. Valida que la categoría sea `'Primera'` o `'Máxima'`. En `POST /equipos` y `PUT /equipos/{id_equipo}`, verifica duplicados contra los nombres sanitizados en la base de datos para prevenir variantes como `" Barcelona "` o `"BARCELONA  FC"`.
- **Frontend (`AdminDashboard.vue`):** Helper `normalizarNombreEquipo(valor)` formatea textos en el formulario. La categoría por defecto es `'Primera'`.

### 2. Validación Estricta de Cédulas Ecuatorianas
- **Reglas del Registro Civil:**
  - Exactamente 10 dígitos numéricos (`^\d{10}$`).
  - Código de provincia: **`01` a `24`** (provincias) o **`30`** (Ecuatorianos residentes en el exterior).
  - Tercer dígito: **`0` a `5`** (persona natural).
  - Verificación del décimo dígito mediante algoritmo Módulo 10.
- **Implementación:** `validar_cedula_ecuatoriana` en `main.py`, y `validarChecksumCedula` en `AdminDashboard.vue` y `Registro.vue`.

### 3. Configuración CORS Dinámica
- `CORSMiddleware` en `main.py` está configurado con `allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?"` y orígenes explícitos (`http://localhost:5173`, `http://127.0.0.1:5173`) permitiendo `allow_credentials=True` sin errores de origen cruzado en navegadores.

### 4. Tarjeta de Marcador Deportivo (Estilo `marcador.png` en Paleta Blanco y Azul)
- Formato inspirado en marcadores deportivos tipo Google Sports / OneFootball:
  - Header: `⚽ LigaConocoto • Fecha • Categoría` (izquierda) y Estado `Finalizado` / `⏰ Hora` (derecha).
  - Marcador central: Escudo local (56px) + Nombre -> Marcador numérico destacado (`text-3xl md:text-4xl font-mono font-black text-[#001a4d] bg-blue-50`) -> Escudo visitante + Nombre.
  - Paleta de colores institucional en blanco (`bg-white`), azul marino (`text-[#001a4d]`), bordes en azul tenue (`border-2 border-blue-100`) y acentos amarillos.
- Implementado en [AdminDashboard.vue](file:///C:/Users/Det-Pc/Desktop/LigaDeportivaBarrial/frontend-liga-vue/src/views/AdminDashboard.vue) (Cronograma Oficial) e [Inicio.vue](file:///C:/Users/Det-Pc/Desktop/LigaDeportivaBarrial/frontend-liga-vue/src/views/Inicio.vue) (Calendario Oficial).

### 5. Registro de Presidente de Equipo y Vinculación con Traspasos
- **Base de Datos & Backend (`ensure_schema.py`, `main.py`):** Se añadió la columna `Presidente` (`NVARCHAR(150) NULL`) en la tabla `Equipos`. Los endpoints `GET /equipos`, `POST /equipos` y `PUT /equipos/{id_equipo}` soportan la recepción, guardado y actualización del nombre del presidente o representante legal del club.
- **Frontend (`AdminDashboard.vue`):**
  - **Panel de Equipos:** Formulario con campo para "Presidente / Dirigente" y columna en la tabla de Equipos Registrados.
  - **Módulo de Traspasos:** Muestra a los presidentes autorizantes del equipo de origen y del equipo de destino en tiempo real al seleccionar jugador y nuevo club.

### 6. Documentación
- [README.md](file:///C:/Users/Det-Pc/Desktop/LigaDeportivaBarrial/README.md) en la raíz contiene el resumen completo de la arquitectura del proyecto, endpoints API y guía de instalación.

---

## Data Model (SQL Server `LigaConocotoDB`)
Core tables: `Equipos` (contiene `Presidente`), `Jugadores` (FK → `Equipos`), `Arbitros`, `Usuarios` (FK → `Jugadores`, holds `Rol`), `Partidos` (FK → `Equipos` x2 local/visitante, FK → `Arbitros` x3), `Estadisticas_Jugadores`, `Asistencia`, `Suspensiones_Jugadores`, `Calificaciones_Arbitros`. `Jugadores.Cedula` and `Arbitros.Cedula` cross-check against each other.

---

## Secrets & Config
- `firebase-key.json` required at repo root for Firebase Storage.
- `database.py` connects to local SQL Server instance `DESKTOP-A9DPDLM\SQLNEY` database `LigaConocotoDB`.
