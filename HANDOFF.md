# BetML Pro — Estado al 2026-08-11

Sesión larga, backend pasó de ~50% a prácticamente completo. Este doc es
para retomar después de `/clean` sin releer todo el historial.

## Qué hay que revisar apenas retomes

1. **Reentreno de modelos — TODAVÍA CORRIENDO** al cerrar esta sesión
   (job `bm0mppj32`), última marca vista: 6000/16422 partidos del
   dataset regenerándose (empezó 10:18, a este ritmo termina la parte de
   dataset ~10:55-11:00, después XGBoost/MLP/LSTM/GNN son rápidos, unos
   minutos más). Verificar al retomar:
   ```
   tail -50 "C:\Users\USER\AppData\Local\Temp\claude\C--Users-USER-Desktop-Proyectosy-Folders-BETML-BetML-Pro\fb8a7bd4-fe8c-4b15-b7ea-1a35cdd1732a\scratchpad\reentreno_completo.log"
   ```
   Si terminó bien, busca la línea `"Reentrenamiento completo"` al
   final. Si el proceso murió a mitad (se cerró la sesión, PC se
   durmió, etc), correr de nuevo desde cero:
   ```
   .venv\Scripts\python.exe -m backend.pipeline.job_reentrenar_modelos
   ```

2. **Graphify actualizado — YA TERMINÓ.** 846 nodos, 1572 edges, 71
   comunidades (era 537/877 al inicio de la sesión). `graphify-out/graph.json`
   al día con todo lo construido hoy.

## Por qué no encontraba el partido de "hoy" (la duda que quedó pendiente)

**No hay cron corriendo en producción todavía.** Todo lo que trae
partidos/stats/cuotas del día (`backend/scheduler/scheduler.py`) está
escrito y probado, pero nadie lo tiene ejecutándose 24/7 — ni deploy, ni
Task Scheduler de Windows, ni nada. Por eso la BD no tiene el partido de
Bodo/Glimt vs Union St. Gilloise de hoy: nadie corrió `pipeline_dia.py`
hoy. Esto es esperado, no bug — falta poner el scheduler a correr en
algún lado (ver sección Deploy).

## Arquitectura completa — qué existe y dónde

### Pipeline de datos (backend/pipeline/)
- `pipeline_dia.py` — fixtures del día (API-Football, gratis, por fecha)
- `job_estadisticas.py` — stats API-Football de partidos ya jugados
- `backend/pipeline/sofascore/job_sofascore.py` — stats Sofascore diarias
  (xG, corners, jugadores) — reescrito esta sesión, el endpoint viejo por
  fecha estaba muerto, ahora usa página 0 por liga+temporada vigente
- `backend/pipeline/sofascore/job_historico_sofascore.py` — backfill
  histórico completo (23/24, 24/25), ya corrido, 96%+ cobertura
- `backend/pipeline/sofascore/job_crear_fixtures_sofascore.py` — crea
  partidos NUEVOS desde Sofascore (25/26 + Mundial 2026, API-Football
  free no llega a esas temporadas) — ya corrido
- `job_odds.py` — cuotas reales GRATIS de API-Football por `fixture_id`
  (bypasea el gate de plan free que bloquea league+season). 14
  bookmakers, ~200 mercados por partido
- `job_cerrar_predicciones.py` — MLOps: cierra predicciones Y parlays
  pendientes contra resultado real
- `job_reentrenar_modelos.py` — reentrena los 4 modelos + Dixon-Coles,
  agendado semanal (domingo 3am)

### Scheduler (backend/scheduler/scheduler.py)
Todo agendado, nada corriendo en prod:
```
23:55 → pipeline_dia (fixtures de hoy)
00:30 → job_estadisticas (stats API-Football)
00:45 → fixtures de mañana
01:00 → job_sofascore_diario
01:15 → job_odds
01:30 → job_cerrar_predicciones
Domingo 03:00 → job_reentrenar_modelos
```

### Modelos ML (backend/models/)
- `entrenador.py` — XGBoost, class-balanced (Empate no colapsa), calibrado
- `mlp.py` — MLP multiobjetivo (1X2, Over2.5, BTTS, corners/tarjetas
  regresión, HT) — PyTorch
- `lstm.py` — LSTM bidireccional + atención temporal, secuencias de
  últimos 10 partidos por equipo
- `gnn.py` — GNN equipo-jugador (torch_geometric, HeteroConv), grafo
  transductivo (limitación conocida, documentada en el archivo)
- `ensemble.py` — combina los 4 por accuracy de validación
- `calibracion.py` — regresión isotónica sobre XGBoost
- `montecarlo.py` — Poisson bivariado + Dixon-Coles (rho ajustado por
  MLE con datos reales, no el default de literatura), handicap
  asiático, split 1er/2do tiempo
- `kelly.py` — Kelly fraccionario, todos los mercados, factor_confianza
  por calibración
- `kelly_portfolio.py` — Kelly de portafolio (mercados correlacionados
  del mismo partido, vía escenarios Monte Carlo) + probabilidad de ruina
- `parlay.py` — combinadas entre partidos DISTINTOS (asume independencia)
- `resolver_mercado.py` — dado un partido FT, resuelve si CUALQUIER
  mercado ganó o perdió (para MLOps)
- `parser_imagen.py` — OCR gratis (easyocr) de capturas de parley +
  matching a partido real. **OJO: tiene guardrail de fecha — si el
  partido más cercano en BD está a más de 3 días de hoy, rechaza en vez
  de usarlo como si fuera el actual** (bug real encontrado y arreglado
  esta sesión)
- `jugadores_montecarlo.py` — mercados de jugador (tiros, goles,
  tarjetas) para el XI probable

### Features (backend/features/)
- `calculador.py` — todo el feature engineering, sin leakage (ojo:
  `rating_local`/`rating_visit` tenían leakage grave, arreglado)
- `dataset.py` — genera dataset ML, cachea a disco
  (`data/dataset_features.pkl`)
- `grafo.py` — construye el grafo equipo-jugador para la GNN
- `jugadores.py` — features de jugador individual (XI probable,
  promedios históricos)

### API (backend/api/)
Todo bajo JWT excepto `/auth/*`. Endpoints en `predicciones.py`:
- `GET /predicciones/{id}/ensemble`
- `GET /predicciones/{id}/kelly` (?guardar=true para trackear)
- `GET /predicciones/{id}/kelly/portafolio`
- `GET /predicciones/{id}/montecarlo`
- `GET /predicciones/{id}/jugadores`
- `POST /predicciones/combinada` (parlay entre partidos distintos)
- `POST /predicciones/analizar-captura` (subís imagen de parley, te dice
  probabilidad/recomendación de cada pata)
- `GET /stats/modelo` (accuracy por mercado + parlays)
- `POST /auth/registro`, `/auth/login`, `GET /auth/me`

### DB — tablas nuevas esta sesión
`Odds`, `Usuario`, `Parlay`, `ParlaySeleccion`. Además: `Partido.sofascore_id`,
`Equipo.sofascore_id`, `EstadisticaJugador.equipo_id` (estaba 100% vacío,
backfilleado — bug de `parser.py` que leía el id de Sofascore en vez del
nuestro, ARREGLADO en el origen también).

### Tests
`tests/` — 35 tests, pytest, corren en ~5-15s (`pytest tests/ -q`).
Cubren Kelly, portafolio, parlay, Montecarlo, auth, MLOps, parser de
imagen. Todo en verde a la fecha de este doc.

## Gaps conocidos, honestos, sin resolver

1. **Nada corriendo en producción** — el scheduler existe pero no está
   deployado en ningún lado. Es la causa de "no encuentra partidos de
   hoy". Decidir: VPS propio, Task Scheduler de Windows local, o cloud
   (Render/Railway/etc con un worker).
2. **Cobertura de fases clasificatorias de copas europeas** — Champions/
   Europa/Conference League qualifying rounds tienen huecos reales (son
   torneos "escondidos" bajo otro `unique-tournament` id en Sofascore
   que nunca se mapeó). Afecta partidos como el de Bodo/Glimt de hoy.
3. **Frontend Flutter existe pero apunta a los endpoints VIEJOS** —
   `frontend/` tiene 3 pantallas (home/detalle/stats) de antes de esta
   sesión. Ensemble, Kelly-portafolio, parlay, análisis de imagen,
   jugadores: nada de eso está conectado en el front todavía.
4. **`parser_imagen.py` es heurístico** — probado con imagen sintética
   limpia, no con capturas reales de bookmakers variados. Puede fallar
   con layouts raros — lista lo que no reconoce en vez de inventar, pero
   la cobertura real de "qué tanto entiende" no está medida en producción.
5. **Deploy (Docker/Nginx/systemd) no se tocó** — decisión explícita del
   usuario de saltarlo por ahora.
6. **Accuracy real ronda 44-51% en 1X2** — es lo esperable en fútbol
   pre-partido, no es un bug a perseguir. Empate ya no colapsa a 0%
   gracias al class weighting.

## Deuda técnica menor (ponytail: comentarios en el código)
- `gnn.py`: grafo transductivo de una sola foto, no por-partido —
  documentado en el propio archivo con upgrade path (snapshots por
  temporada si hace falta).
- `montecarlo.py`/corners/tarjetas: Poisson independiente, sin
  correlación tipo Dixon-Coles (no hay evidencia de que aplique igual).

## Cómo retomar rápido
```bash
# ver que el reentreno/graphify terminaron bien
cat data/models/metricas_xgboost.pkl  # o similar, revisar fecha mod
graphify god-nodes --top 15

# correr tests
.venv\Scripts\python.exe -m pytest tests/ -q

# levantar API local para probar
.venv\Scripts\python.exe -m uvicorn backend.api.main:app --reload
```

Preguntas abiertas para el usuario cuando retome:
- ¿Dónde deployamos el scheduler? (define si "hoy" empieza a funcionar)
- ¿Atacamos el hueco de qualifying rounds de copas europeas?
- ¿Empezamos a conectar el frontend a los endpoints nuevos?
