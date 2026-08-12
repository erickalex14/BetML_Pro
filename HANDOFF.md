# BetML Pro — Estado al 2026-08-12

Sesión larga: backend ganó explicabilidad + tab de recomendadas; frontend
pasó de 3 pantallas viejas a app completa (auth, redesign, todos los
endpoints conectados). Este doc es para retomar después de `/clear` sin
releer todo el historial.

## Qué hay que revisar apenas retomes

1. **Nada de esta sesión está commiteado en git.** Todo lo de abajo —
   redesign completo, auth, recomendadas, explicabilidad, fixes — sigue
   en el working tree sin commit. Revisar `git status` y decidir cómo
   trocear los commits antes de seguir tocando código.
2. **Backend corre en puerto 8001** (no 8000 — hubo conflictos de puerto
   esta sesión). Front (Flutter web) corre en puerto **5050**.
   `--reload` de uvicorn es poco confiable en este entorno
   (Windows + path con espacios) — solo agarró 1 de varios cambios en
   varias pruebas. Reiniciar manualmente después de cada cambio backend:
   ```
   .venv\Scripts\python.exe -m uvicorn backend.api.main:app --port 8001
   ```
   Frontend, igual, reiniciar manual tras cada cambio:
   ```
   cd frontend && flutter run -d web-server --web-port=5050 --web-hostname=localhost
   ```
3. **Tab "Recomendadas" (GET /predicciones/recomendadas) construida y
   verificada por script, pero el usuario todavía NO la vio corriendo en
   la app en vivo.** Es lo primero para confirmar en cuanto retomes:
   abrir `http://localhost:5050`, tab "Top" en el bottom nav, revisar
   que carguen individuales/combinadas/parlays sin error.
4. **Sofascore: no se encontró endpoint para "próximos partidos por
   liga".** `/events/last/` solo trae pasados, `/events/next/{pagina}`
   (probado, adivinado) da 404. Esto bloquea el auto-anchoring de
   `sofascore_id` para partidos que aún no se jugaron fuera del rango
   que ya cubre `TEMPORADAS_HISTORICAS`. Reportado honesto al usuario,
   sin respuesta aún sobre si seguir insistiendo o dejarlo así.
5. **Graphify actualizado — YA TERMINÓ (solo AST, sin LLM).** 1479
   nodos, 2620 edges, 95 comunidades (era 846/1572/71 al cierre de la
   sesión anterior). `graphify-out/graph.json` al día con todo el código
   nuevo/modificado de hoy. Nota: el `graphify` CLI global (`~/.local/bin`)
   no tenía el intérprete resuelto (`.graphify_python` faltaba) —
   se reinstaló `graphifyy` sobre
   `C:\Users\USER\AppData\Local\Programs\Python\Python311\python`.
   Si vuelve a faltar, reinstalar con
   `python -m pip install --upgrade graphifyy`.

## Qué se hizo esta sesión (resumen denso)

### Backend — ML / explicabilidad
- **Ensemble pondera por accuracy real**, no fijo — `_peso_modelo()` en
  `backend/models/ensemble.py`, umbral `MIN_MUESTRAS_PESO=20` con
  fallback a accuracy de validación si no hay muestras suficientes.
  Cada modelo individual también se persiste (`mercado="1X2-{nombre}"`)
  para que `job_cerrar_predicciones.py` los cierre igual (usa
  `startswith("1X2")` en vez de match exacto).
- **`backend/models/explicacion.py` (nuevo)** — generador determinístico
  de "por qué" (sin LLM). `generar_resumen()` compara forma/xG/tiros/
  posesión/rating por factor, `generar_resumen_h2h()` para historial
  directo. Conectado en `prediccion_service.py` → cada predicción trae
  `factores` y `resumen_h2h`.
- **Jugadores**: `jugadores_montecarlo.py` simula ahora asistencias,
  pases, duelos (antes solo tiros). `obtener_lineup_confirmada()` en
  `features/jugadores.py` usa alineación confirmada real (si existe)
  antes de caer al XI probable heurístico.

### Backend — tab "Recomendadas" (feature nueva de hoy)
`GET /predicciones/recomendadas?bankroll=&fraccion=&n_simulaciones=&top_individuales=`
en `backend/api/routes/predicciones.py`. Devuelve:
- `apuestas_individuales` — value bets sueltas, ordenadas por EV, top N.
- `combinadas_mismo_partido` — portafolio Kelly de mercados
  correlacionados del MISMO partido (vía Monte Carlo con escenarios).
- `parlays_sugeridos` — combinadas 2/3/4 patas entre partidos DISTINTOS,
  arma con el mejor mercado de cada partido candidato.
Excluye ligas en `LIGAS_SIN_HISTORIAL_ID` (amistosos — ver abajo) porque
sin historial real el modelo infla EV falsamente (se vio un caso real:
365% EV falso en amistoso, por eso el filtro).
Verificado a mano con datos reales antes de conectar el front — 2 bugs
reales encontrados y arreglados en el camino (KeyError `_escenarios` por
usar el montecarlo equivocado; colisión de key `selecciones` al mezclar
dicts con `**resultado`).

### Backend — reentreno diario
`scheduler.py`: `job_reentrenar_modelos` pasó de
`schedule.every().sunday.at("03:00")` a **`schedule.every().day.at("03:00")`**
(pedido explícito del usuario — modelos frescos todos los días de
madrugada, no solo domingo). También agregado `job_alineaciones()` cada
15 min (ver amistosos/lineups abajo).

### Backend — amistosos (Friendlies) visibles sin contaminar forma
Decisión del usuario vía pregunta directa: **visibles en la lista de
partidos, pero excluidos de todo cálculo de forma/historial**. Se agregó
`"Friendlies": 10` y `"Friendlies Clubs": 667` a `LIGAS` en
`pipeline/config.py`, más constante `LIGAS_SIN_HISTORIAL_ID = {10, 667}`.
Ese set se usa como filtro (`liga_id.notin_(...)`) en las 10+ queries de
historial en `features/calculador.py` y `features/jugadores.py` — forma,
xG, tiros, posesión, rating, H2H, win rate, todo. Y en el filtro de
`/recomendadas` (arriba).

### Backend — alineaciones/plantillas actualizadas
Motivo: usuario reportó jugador (Tonali) mostrado en equipo viejo
(Newcastle) después de transferirse (Tottenham) — plantillas quedaban
stale. Fix real, no parche:
- `guardador_sofascore.py`: `guardar_jugadores()` pasó de "saltar si el
  partido ya tiene alguna fila" a **UPSERT por jugador** (query por
  `partido_id + sofascore_jugador_id`). Antes, una fila pre-partido con
  stats=None bloqueaba para siempre la actualización post-partido con
  stats reales — ahí estaba el stale data.
- `backend/pipeline/sofascore/job_alineaciones.py` (nuevo) — trae
  alineación confirmada de Sofascore para partidos que arrancan dentro
  de 90 min. Usa `ahora_partidos()` (zona America/Guayaquil, ver abajo)
  en vez de UTC. Auto-ancla `sofascore_id` faltante vía
  `TEMPORADAS_HISTORICAS` + matching nombre-equipo+fecha con guardas
  anti-duplicado (evita el `IntegrityError` de unique constraint que
  salió en pruebas — dos partidos distintos, mismos 2 equipos, fechas
  distintas, matcheaban al mismo evento Sofascore sin el chequeo de
  fecha).
  **Pendiente/roto**: el paso de "buscar próximos eventos" no funciona
  para fixtures que aún no se jugaron fuera de ligas oficiales mapeadas
  (ver punto 4 arriba). Se dejó documentado, no se siguió adivinando
  endpoints.

### Backend — otros bugs reales arreglados
- `PartidoService._enriquecer()`: parámetro `con_prediccion` nunca se
  usaba (dead param) — el Home nunca mostraba predicciones por esto.
  Ahora sí llama `PrediccionService.predecir()` cuando `con_prediccion=True`.
- `GET /partidos/{id}`: bypaseaba el service entero, devolvía el ORM
  crudo (sin nombres de equipo — Flutter mostraba "Local"/"Visitante"
  literal). Arreglado a llamar `PartidoService.get_detalle()`.
- `prob_combinada_estimada` en analizar-captura: devolvía falso 100%
  cuando CERO mercados se pudieron calcular (chequeaba lista no-vacía en
  vez de "algo se calculó realmente"). Agregado flag
  `algun_mercado_calculado` + aviso claro cuando `pred is None`.
- Posesión formateada x100 de más (`{:.0%}` sobre valor ya 0-100).
- Equipos duplicados en BD (dos filas "Fluminense") rompían el matching
  de partido en el parser de imagen — ahora se pasan TODOS los
  candidatos fuzzy-match, no solo el top-1.
- Timezone: `datetime.utcnow()` comparado contra `Partido.fecha` (naive,
  guardado en hora local Guayaquil, UTC-5) en `job_partidos_en_vivo.py`
  — creado `ahora_partidos()` en `pipeline/config.py` con
  `zoneinfo.ZoneInfo("America/Guayaquil")`.
- Logos de equipo: `logo_url` de API-Football estaba en la respuesta y
  sin usar — ahora se captura en `guardador.py._upsert_equipo()` y se
  expone en `PartidoService` (`local_logo`/`visitante_logo`).
- UEFA Super Cup (id 531) agregado a `LIGAS` — faltaba, por eso no se
  podía predecir ese partido cuando el usuario preguntó.

### Frontend — construido desde casi cero esta sesión
Auth (JWT, secure storage), redesign completo de diseño (paleta derivada
de los logos reales del usuario — navy/blue/lime —, NO genérica/AI-looking,
inspirado sin copiar en Betano/SofaScore, claymorphism limitado a ≤2
momentos por pantalla, JetBrains Mono para números/scores). Pantallas:
login, home, detalle, análisis avanzado (Kelly por categoría, jugadores,
Montecarlo), stats, perfil, mis-predicciones, parlay builder,
analizar-captura (sube imagen), y la nueva recomendadas.
- 5 tabs en bottom nav: Partidos / Top (recomendadas) / Mías / Stats / Perfil.
- Logos de equipo reales (`TeamLogo` widget, fallback a inicial si la
  imagen falla).
- Entities/models/datasources/repos/usecases nuevos para: análisis de
  imagen, parlay, kelly-mercados, predicciones-mías, guardar-mercados,
  recomendadas — arquitectura limpia (domain/data/presentation)
  consistente con lo que ya existía.
- `flutter analyze` → 0 issues al cierre de la sesión.
- `pytest tests/ -q` → 55 passed al cierre.

## Arquitectura completa — qué existe y dónde

### Pipeline de datos (backend/pipeline/)
- `pipeline_dia.py` — fixtures del día (API-Football, gratis, por fecha)
- `job_estadisticas.py` — stats API-Football de partidos ya jugados
- `job_partidos_en_vivo.py` — polling en vivo, timezone-fixed esta sesión
- `sofascore/job_sofascore.py` — stats Sofascore diarias (xG, corners,
  jugadores)
- `sofascore/job_historico_sofascore.py` — backfill histórico (23/24,
  24/25), 96%+ cobertura
- `sofascore/job_crear_fixtures_sofascore.py` — crea partidos nuevos
  desde Sofascore (25/26 + Mundial 2026)
- `sofascore/job_alineaciones.py` — **nuevo esta sesión**, alineación
  confirmada 90 min antes del partido (ver gaps arriba)
- `job_odds.py` — cuotas reales gratis vía `fixture_id`
- `job_cerrar_predicciones.py` — cierra predicciones y parlays contra
  resultado real (MLOps)
- `job_reentrenar_modelos.py` — reentrena los 4 modelos + Dixon-Coles,
  **ahora diario 3am** (antes semanal)

### Scheduler (backend/scheduler/scheduler.py)
```
23:55 → pipeline_dia (fixtures de hoy)
00:30 → job_estadisticas
00:45 → fixtures de mañana
01:00 → job_sofascore_diario
01:15 → job_odds
01:30 → job_cerrar_predicciones
03:00 diario → job_reentrenar_modelos   (antes: solo domingo)
cada 15 min → job_alineaciones          (nuevo)
```
Sigue sin estar deployado en producción 24/7 (VPS Ubuntu on-premise es
el plan, decisión ya tomada por el usuario — falta ejecutarlo).

### Modelos ML (backend/models/)
- `entrenador.py`, `mlp.py`, `lstm.py`, `gnn.py`, `ensemble.py`
  (**pondera por accuracy real ahora**, ver arriba)
- `calibracion.py`, `montecarlo.py`, `kelly.py`, `kelly_portfolio.py`,
  `parlay.py`, `resolver_mercado.py`, `parser_imagen.py`
- `jugadores_montecarlo.py` — extendido (asistencias/pases/duelos)
- `explicacion.py` — **nuevo**, explicabilidad determinística

### Features (backend/features/)
- `calculador.py`, `dataset.py`, `grafo.py` — sin cambios de fondo
- `jugadores.py` — `obtener_lineup_confirmada()` nuevo, forma extendida

### API (backend/api/) — endpoints nuevos/cambiados esta sesión
- `GET /predicciones/recomendadas` — **nuevo**, la tab del pedido de hoy
- `GET /predicciones/mias` — **nuevo**, historial de predicciones
  guardadas (filtro por estado)
- `POST /predicciones/{id}/guardar-mercados` — **nuevo**, guarda
  mercados elegidos como Predicciones trackeadas
- `GET /partidos/{id}` — **arreglado**, ahora pasa por PartidoService

### DB
Sin tablas nuevas esta sesión (las de la sesión anterior — Odds,
Usuario, Parlay, ParlaySeleccion — siguen igual).

### Tests
`tests/` — **55 tests**, pytest. Nuevos: `test_explicacion.py`,
`test_partido_service.py`, `test_alineaciones.py`, extendido
`test_parser_imagen.py` (duplicados de equipo).

## Gaps conocidos, honestos, sin resolver
1. **Nada en producción** — scheduler completo pero no deployado. Plan
   ya decidido (VPS Ubuntu on-premise del usuario), falta ejecutar.
2. **Sofascore "próximos partidos" no tiene endpoint encontrado** — ver
   punto 4 arriba. Bloquea auto-anchoring de `sofascore_id` para
   fixtures futuros fuera de `TEMPORADAS_HISTORICAS`, y no funciona en
   absoluto para amistosos.
3. **Qualifying rounds de copas europeas** — huecos de cobertura, torneo
   "escondido" bajo otro id en Sofascore, sin mapear.
4. **`parser_imagen.py` heurístico** — cobertura real contra capturas
   variadas de bookmakers no medida en producción.
5. **Git: todo sin commitear** — ver punto 1 arriba.
6. **Nada de esto se vio corriendo en la app en vivo todavía** (salvo
   por prints/scripts de verificación manual) — falta la pasada de QA
   visual completa en el navegador.

## Cómo retomar rápido
```bash
# backend
.venv\Scripts\python.exe -m uvicorn backend.api.main:app --port 8001

# frontend
cd frontend && flutter run -d web-server --web-port=5050 --web-hostname=localhost

# tests
.venv\Scripts\python.exe -m pytest tests/ -q
flutter analyze   # desde frontend/

# graphify (si vuelve a faltar el intérprete)
python -m pip install --upgrade graphifyy
```

Preguntas abiertas para el usuario cuando retome:
- ¿Commiteamos todo lo de hoy ya, o seguimos acumulando?
- ¿Insistimos en encontrar el endpoint de Sofascore para próximos
  partidos, o dejamos el auto-anchoring solo para ligas ya mapeadas?
- ¿Hacemos la pasada de QA visual completa de la tab Recomendadas y el
  resto del redesign antes de seguir con features nuevas?
