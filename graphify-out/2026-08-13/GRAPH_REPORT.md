# Graph Report - BetML_Pro  (2026-08-12)

## Corpus Check
- 161 files · ~262,637 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1479 nodes · 2620 edges · 95 communities (88 shown, 7 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 54 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1d1ac386`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- simular_partido
- test_auth.py
- database.py
- PartidoRepository
- get_detalle_partido.dart
- scheduler.py
- job_reentrenar_modelos.py
- ensemble.py
- PrediccionRepository
- lstm.py
- partido.dart
- prediccion.dart
- AppDelegate
- test_parser_imagen.py
- SofascoreCliente
- predicciones.py
- calculador.py
- mlp.py
- job_historico_sofascore.py
- theme.dart
- home_screen.dart
- get
- constants.dart
- job_cerrar_predicciones.py
- detalle_screen.dart
- partidos_provider.dart
- simular_jugadores_partido
- job_crear_fixtures_sofascore.py
- stats_provider.dart
- test_alineaciones.py
- stats_screen.dart
- manifest.json
- partido_repo_impl.dart
- analisis_avanzado_screen.dart
- analisis_avanzado.dart
- main.dart
- failures.dart
- recomendadas.dart
- router.dart
- parlay_screen.dart
- auth_remote_ds.dart
- login_screen.dart
- package:flutter/material.dart
- FlutterActivity
- modelos.py
- mis_predicciones_screen.dart
- recomendadas_screen.dart
- BetML_Pro_Informe_Tecnico_v3.md
- ../../core/errors/failures.dart
- analizar_captura_screen.dart
- job_alineaciones.py
- .predecir
- Partido
- Prediccion
- PartidoService
- analisis_avanzado_model.dart
- analisis_imagen.dart
- clay.dart
- Arquitectura completa — qué existe y dónde
- parlay.dart
- auth_provider.dart
- _necesita_actualizacion
- job_odds.py
- partido_remote_ds.dart
- api_client.py
- analisis_remote_ds.dart
- String?
- analisis_repo_impl.dart
- analisis_imagen_model.dart
- ../../domain/entities/parlay.dart
- frontend
- LaunchImage.imageset/README.md
- bool?
- DateTime?

## God Nodes (most connected - your core abstractions)
1. `Partido` - 39 edges
2. `PartidoRepository` - 35 edges
3. `PrediccionRepository` - 32 edges
4. `get()` - 27 edges
5. `PrediccionService` - 27 edges
6. `SofascoreCliente` - 26 edges
7. `simular_partido()` - 24 edges
8. `crear_tablas()` - 22 edges
9. `predecir_ensemble()` - 21 edges
10. `PartidoService` - 19 edges

## Surprising Connections (you probably didn't know these)
- `registro()` --references--> `_post`  [EXTRACTED]
  backend/api/routes/auth.py → frontend/lib/data/datasources/auth_remote_ds.dart
- `login()` --references--> `_post`  [EXTRACTED]
  backend/api/routes/auth.py → frontend/lib/data/datasources/auth_remote_ds.dart
- `test_token_invalido_rechazado()` --calls--> `verificar_token()`  [EXTRACTED]
  tests/test_auth.py → backend/core/auth.py
- `_equipo_temporal()` --calls--> `Equipo`  [EXTRACTED]
  tests/test_alineaciones.py → backend/db/modelos.py
- `_partido_temporal()` --calls--> `Partido`  [EXTRACTED]
  tests/test_alineaciones.py → backend/db/modelos.py

## Import Cycles
- None detected.

## Communities (95 total, 7 thin omitted)

### Community 0 - "simular_partido"
Cohesion: 0.06
Nodes (56): factor_confianza(), Cuánto confiar en la calibración de esta clase en este rango de probabilidad,…, analizar_mercados_kelly(), calcular_kelly(), _expandir_over_under(), probabilidad_ruina(), Kelly de portafolio — para cuando se apuesta a VARIOS mercados del MISMO…, Simula qué pasa si esta MISMA combinación de apuestas (mismos stakes) se repite… (+48 more)

### Community 1 - "test_auth.py"
Cohesion: 0.08
Nodes (41): health(), root(), startup(), login(), LoginRequest, me(), BaseModel, Session (+33 more)

### Community 2 - "database.py"
Cohesion: 0.20
Nodes (14): crear_tablas(), guardar_partido(), Session, Crea el equipo si no existe. Si ya existe pero le falta el logo (723 equipos ya…, _upsert_equipo(), correr_job_historico(), correr_job_temporada_actual(), _parsear_estadisticas() (+6 more)

### Community 3 - "PartidoRepository"
Cohesion: 0.16
Nodes (6): PartidoRepository, Partido, Session, get_modelo_service(), Session, date

### Community 4 - "get_detalle_partido.dart"
Cohesion: 0.12
Nodes (17): ../entities/partido.dart, ../entities/prediccion.dart, ../entities/recomendadas.dart, PartidoRepositoryImpl, PartidoRepository, GetDetallePartido, _repository, GetPartidosHoy (+9 more)

### Community 5 - "scheduler.py"
Cohesion: 0.13
Nodes (22): correr_job_estadisticas(), correr_job_odds(), correr_job_sofascore_diario(), iniciar_scheduler(), job_alineaciones(), job_cerrar_predicciones(), job_estadisticas(), job_fixtures_manana() (+14 more)

### Community 6 - "job_reentrenar_modelos.py"
Cohesion: 0.11
Nodes (23): generar_dataset(), DataFrame, construir_grafo(), Construcción del grafo equipo-jugador para la GNN. Dos tipos de nodo (equipo,…, Devuelve (grafo, id_a_indice_equipo, id_a_indice_jugador). fecha_corte=None usa…, guardar_modelo(), cargar_gnn(), entrenar_gnn() (+15 more)

### Community 7 - "ensemble.py"
Cohesion: 0.13
Nodes (25): ajustar_calibracion(), calibrar_probabilidades(), cargar_calibracion(), guardar_calibracion(), ndarray, Path, Calibración de probabilidades del modelo — necesaria para que Kelly tenga…, Aplica el calibrador de cada clase y renormaliza a que sume 1. (+17 more)

### Community 8 - "PrediccionRepository"
Cohesion: 0.09
Nodes (26): Prediccion, _peso_modelo(), Session, correr_job_cerrar_predicciones(), PrediccionRepository, Prediccion, Session, Cierra UNA predicción puntual, ya resuelta externamente (ver… (+18 more)

### Community 9 - "lstm.py"
Cohesion: 0.11
Nodes (15): cargar_lstm(), CodificadorTemporal, _DatasetSecuencias, guardar_lstm(), _pad_izquierda(), predecir_lstm(), DataFrame, Dataset (+7 more)

### Community 10 - "partido.dart"
Cohesion: 0.08
Nodes (24): enJuego, estado, fecha, golesLocal, golesVisit, hora, id, jornada (+16 more)

### Community 11 - "prediccion.dart"
Cohesion: 0.06
Nodes (33): double get, accuracy, accuracyStr, acertadas, acerto, altaConfianza, confianza, creadoEn (+25 more)

### Community 12 - "AppDelegate"
Cohesion: 0.11
Nodes (14): Any, Flutter, FlutterAppDelegate, FlutterImplicitEngineBridge, FlutterImplicitEngineDelegate, FlutterSceneDelegate, AppDelegate, Bool (+6 more)

### Community 13 - "test_parser_imagen.py"
Cohesion: 0.16
Nodes (20): analizar_captura_parley(), _clasificar_over_under(), _detectar_categoria(), _es_btts(), _es_resultado_partido(), extraer_texto(), _get_lector(), _linea_a_clave() (+12 more)

### Community 14 - "SofascoreCliente"
Cohesion: 0.09
Nodes (15): Cliente de Sofascore usando Playwright. Lanza un browser Chromium real para…, Arranca el browser y visita Sofascore para obtener cookies., Cierra el browser limpiamente., Hace una request a la API de Sofascore usando el browser. Navega directamente a…, Trae todos los partidos de fútbol de una fecha., Trae estadísticas completas de un partido., Trae alineaciones y stats de jugadores., Trae partidos históricos (ya jugados) de una liga y temporada — /events/last/,… (+7 more)

### Community 15 - "predicciones.py"
Cohesion: 0.10
Nodes (40): analizar_captura(), apuesta_combinada(), _correr_montecarlo_partido(), guardar_mercados(), GuardarMercadosRequest, kelly_partido(), kelly_portafolio_partido(), montecarlo_partido() (+32 more)

### Community 16 - "calculador.py"
Cohesion: 0.24
Nodes (14): calcular_forma(), calcular_h2h(), calcular_rating_jugadores(), calcular_stats_sofascore(), calcular_win_rate(), construir_features_partido(), obtener_secuencia_equipo(), Partido (+6 more)

### Community 17 - "mlp.py"
Cohesion: 0.18
Nodes (11): cargar_mlp(), _DatasetMultiObjetivo, entrenar_mlp(), _perdida_batch(), DataFrame, Dataset, Path, Red neuronal MLP multiobjetivo — predice 1X2, Over/Under 2.5, BTTS, corners y… (+3 more)

### Community 18 - "job_historico_sofascore.py"
Cohesion: 0.12
Nodes (23): EstadisticaSofascore, Stats avanzadas del partido desde Sofascore. xG, presiones, duelos, pases…, main(), anclar_si_corresponde(), Una vez confirmado (por cruce con Partido: rival+fecha) cuál candidato era el…, guardar_jugadores(), guardar_stats_sofascore(), Session (+15 more)

### Community 19 - "theme.dart"
Cohesion: 0.05
Nodes (42): AppColors get, BuildContext, Color bg, bg2,, Color brick,, Color ledger,, Color line,, Color pitch,, Color shadowDark, (+34 more)

### Community 20 - "home_screen.dart"
Cohesion: 0.07
Nodes (36): dart:async, double width,, _EquipoSeccion, _JugadoresTab, _JugadorRow, _MensajeError, _MercadoKellyRow, _MercadosPorCategoria (+28 more)

### Community 21 - "get"
Cohesion: 0.17
Nodes (15): detalle_partido(), partidos_hoy(), partidos_liga(), prediccion_partido(), Session, mercados_jugadores(), prediccion_ensemble(), predicciones_mias() (+7 more)

### Community 22 - "constants.dart"
Cohesion: 0.08
Nodes (25): analizarCaptura, ApiConstants, AppConstants, appName, appVersion, authLogin, authMe, authRegistro (+17 more)

### Community 23 - "job_cerrar_predicciones.py"
Cohesion: 0.22
Nodes (12): Partido, Resuelve si una selección de cualquier mercado ganó o perdió, dado el resultado…, True si la selección ganó, False si perdió, None si no se puede resolver…, resolver_mercado(), _resultado_1x2(), _stats(), _cerrar_parlays_pendientes(), _cerrar_predicciones_individuales() (+4 more)

### Community 24 - "detalle_screen.dart"
Cohesion: 0.08
Nodes (25): ../../domain/usecases/get_detalle_partido.dart, build, _cargando, _cargar, child, _Contenido, createState, DetalleScreen (+17 more)

### Community 25 - "partidos_provider.dart"
Cohesion: 0.14
Nodes (13): ../../domain/usecases/get_partidos_hoy.dart, _cargando, cargarPartidosHoy, _error, _fecha, _getPartidosHoy, _ligaFiltro, ligasDisponibles (+5 more)

### Community 26 - "simular_jugadores_partido"
Cohesion: 0.29
Nodes (9): calcular_forma_jugador(), obtener_titulares_probables(), Session, Jugadores titulares en al menos min_apariciones (40% default) de los últimos…, Promedio de stats del jugador en sus últimos n partidos disputados antes de…, Simulación Monte Carlo de mercados individuales de jugador — tiros, tiros al…, Simula mercados individuales para el XI de ambos equipos. Usa la alineación…, simular_jugador() (+1 more)

### Community 27 - "job_crear_fixtures_sofascore.py"
Cohesion: 0.19
Nodes (12): buscar_candidatos(), equipos_de_la_liga(), id en NUESTRA BD de una liga por nombre (distinto del id de Sofascore usado…, Query base de equipos, acotada a los que ya jugaron en esta liga (evita que la…, Devuelve [(Equipo, score), ...]. score=None si vino de un sofascore_id ya…, resolver_liga_id(), correr_job_crear_fixtures_sofascore(), _parsear_temporada() (+4 more)

### Community 28 - "stats_provider.dart"
Cohesion: 0.17
Nodes (11): bool get, ../../data/repositories/partido_repo_impl.dart, ../../domain/usecases/get_stats_modelo.dart, StatsModeloModel, StatsModelo, _cargando, cargar, _error (+3 more)

### Community 29 - "test_alineaciones.py"
Cohesion: 0.29
Nodes (11): EstadisticaJugador, obtener_lineup_confirmada(), Features a nivel jugador — para los mercados individuales (tiros, tiros al…, XI real confirmado por Sofascore para ESTE partido (job_alineaciones.py lo trae…, _equipo_temporal(), _limpiar(), _partido_temporal(), Bug real encontrado en sesión: Endrick (ya no juega en Lyon) seguía apareciendo… (+3 more)

### Community 30 - "stats_screen.dart"
Cohesion: 0.15
Nodes (16): ChangeNotifier, AppColors, StatsProvider, build, c, color, createState, initState (+8 more)

### Community 31 - "manifest.json"
Cohesion: 0.18
Nodes (10): background_color, description, display, icons, name, orientation, prefer_related_applications, short_name (+2 more)

### Community 32 - "partido_repo_impl.dart"
Cohesion: 0.12
Nodes (16): ../datasources/partido_remote_ds.dart, ../../domain/entities/partido.dart, ../../domain/entities/prediccion.dart, ../../domain/repositories/partido_repository.dart, PartidoRemoteDataSource, FactorModel, fromJson, MercadoModel (+8 more)

### Community 33 - "analisis_avanzado_screen.dart"
Cohesion: 0.04
Nodes (49): ../../data/repositories/analisis_repo_impl.dart, ../../domain/usecases/get_jugadores_partido.dart, ../../domain/usecases/get_kelly_mercados.dart, ../../domain/usecases/get_kelly_portafolio.dart, ../../domain/usecases/guardar_mercados.dart, _abrirDetalle, _abrirDetalleJugador, _bloqueMercado (+41 more)

### Community 34 - "analisis_avanzado.dart"
Cohesion: 0.04
Nodes (44): asistenciasOverUnder, asistenciasPromedio, clave, cuota, cuotaJusta, edge, entradasOverUnder, entradasPromedio (+36 more)

### Community 35 - "main.dart"
Cohesion: 0.12
Nodes (19): core/router.dart, _auth, BetMLApp, _BetMLAppState, build, createState, main, _router (+11 more)

### Community 36 - "failures.dart"
Cohesion: 0.39
Nodes (7): Failure, mensaje, NetworkFailure, NotFoundFailure, ParseFailure, ServerFailure, statusCode

### Community 37 - "recomendadas.dart"
Cohesion: 0.06
Nodes (38): ../../domain/entities/recomendadas.dart, ApuestaIndividualModel, CombinadaMismoPartidoModel, fromJson, MercadoCombinadaModel, ParlaySugeridoModel, PataParlayModel, RecomendadasModel (+30 more)

### Community 38 - "router.dart"
Cohesion: 0.15
Nodes (12): buildRouter, presentation/providers/auth_provider.dart, ../presentation/screens/analisis_avanzado_screen.dart, ../presentation/screens/analizar_captura_screen.dart, ../presentation/screens/detalle_screen.dart, ../presentation/screens/home_screen.dart, ../presentation/screens/login_screen.dart, ../presentation/screens/mis_predicciones_screen.dart (+4 more)

### Community 39 - "parlay_screen.dart"
Cohesion: 0.08
Nodes (27): ../../data/datasources/parlay_remote_ds.dart, PartidosProvider, build, initState, build, _calculando, _calcular, createState (+19 more)

### Community 40 - "auth_remote_ds.dart"
Cohesion: 0.10
Nodes (22): ../auth_storage.dart, Client, ../../core/constants.dart, dart:convert, AuthClient, _inner, send, AnalisisImagenRemoteDataSource (+14 more)

### Community 41 - "login_screen.dart"
Cohesion: 0.10
Nodes (23): Color, ../../data/datasources/auth_remote_ds.dart, AuthProvider, build, _campo, createState, dispose, _emailCtrl (+15 more)

### Community 42 - "package:flutter/material.dart"
Cohesion: 0.09
Nodes (21): clay.dart, ../../core/theme.dart, dart:math, AppBottomNav, AppTab, build, current, _item (+13 more)

### Community 44 - "modelos.py"
Cohesion: 0.16
Nodes (11): Base, Equipo, EstadisticaPartido, Liga, Odds, Partido, Cuotas reales de casas de apuestas — API-Football /odds (gratis por fixture_id,…, Lectura de cuotas guardadas por job_odds.py — mejor cuota disponible por… (+3 more)

### Community 49 - "mis_predicciones_screen.dart"
Cohesion: 0.10
Nodes (20): ../../domain/usecases/get_predicciones_mias.dart, actual, build, _cargando, _cargar, createState, _error, _filtro (+12 more)

### Community 53 - "recomendadas_screen.dart"
Cohesion: 0.11
Nodes (19): ../../domain/usecases/get_recomendadas.dart, build, _cargando, _cargar, _CombinadasTab, createState, _dato, _datos (+11 more)

### Community 56 - "BetML_Pro_Informe_Tecnico_v3.md"
Cohesion: 0.11
Nodes (18): **1. Estado Actual del Proyecto**, **2.1 Fuente 1 — API-Football**, **2.2 Fuente 2 — Sofascore (Playwright)**, **2.3 Mapeo y Cruce de Fuentes**, **2. Pipeline ETL Dual — API-Football + Sofascore**, **3. Feature Engineering — 36 Variables del Modelo**, **4.1 Modelos de Gradient Boosting (XGBoost + LightGBM)**, **4.2 Red Neuronal MLP — Modelo Multiobjetivo** (+10 more)

### Community 57 - "../../core/errors/failures.dart"
Cohesion: 0.18
Nodes (13): ../../core/errors/failures.dart, ../entities/analisis_avanzado.dart, AnalisisRepositoryImpl, AnalisisRepository, GetJugadoresPartido, _repository, GetKellyMercados, _repository (+5 more)

### Community 58 - "analizar_captura_screen.dart"
Cohesion: 0.12
Nodes (17): dart:typed_data, ../../data/datasources/analisis_imagen_remote_ds.dart, _analizar, AnalizarCapturaScreen, _AnalizarCapturaScreenState, build, _bytes, _cargando (+9 more)

### Community 61 - "job_alineaciones.py"
Cohesion: 0.17
Nodes (15): ahora_partidos(), datetime, Ahora" en la misma zona horaria naive que Partido.fecha — pipeline_dia.py pide…, correr_job_partidos_en_vivo(), _hay_algo_para_actualizar(), Refresca marcador/estado de los partidos de HOY mientras se juegan, y cierra…, _anclar_sofascore_ids(), correr_job_alineaciones() (+7 more)

### Community 64 - ".predecir"
Cohesion: 0.18
Nodes (12): generar_resumen(), generar_resumen_h2h(), Por qué el modelo predijo lo que predijo — sin llamar a un LLM en cada request…, Partido, Genera lista de mercados recomendados según las probabilidades del modelo. Solo…, persistir=True guarda la predicción para tracking de MLOps (ver…, generar_resumen es texto puro sobre números ya calculados — sin DB, sin modelo…, test_caso_parejo_no_fuerza_ganador() (+4 more)

### Community 71 - "PartidoService"
Cohesion: 0.22
Nodes (9): PartidoService, Session, Lógica de negocio relacionada a partidos. Ensambla los datos de múltiples…, Convierte un objeto Partido en dict con datos relacionados. con_prediccion=True…, con_prediccion era un parámetro muerto (bug real encontrado en sesión:…, test_get_detalle_incluye_nombres_reales_no_ids(), test_get_detalle_partido_inexistente_devuelve_none(), test_get_partidos_hoy_cada_fila_trae_clave_prediccion() (+1 more)

### Community 72 - "analisis_avanzado_model.dart"
Cohesion: 0.13
Nodes (14): ../../domain/entities/analisis_avanzado.dart, fromJson, JugadoresPartidoModel, JugadorMercadoModel, KellyAnalisisModel, KellyMercadoModel, KellyPortafolioModel, MercadoPortafolioModel (+6 more)

### Community 73 - "analisis_imagen.dart"
Cohesion: 0.13
Nodes (14): double?, aviso, avisos, cuotaDisponible, edge, mercado, nombreLegible, partidoId (+6 more)

### Community 74 - "clay.dart"
Cohesion: 0.13
Nodes (14): EdgeInsets, build, child, ClayButton, ClayContainer, icon, label, loading (+6 more)

### Community 75 - "Arquitectura completa — qué existe y dónde"
Cohesion: 0.13
Nodes (14): API (backend/api/), Arquitectura completa — qué existe y dónde, BetML Pro — Estado al 2026-08-11, Cómo retomar rápido, DB — tablas nuevas esta sesión, Deuda técnica menor (ponytail: comentarios en el código), Features (backend/features/), Gaps conocidos, honestos, sin resolver (+6 more)

### Community 76 - "parlay.dart"
Cohesion: 0.14
Nodes (13): bankroll, cuotaCombinada, esValueBet, ev, mercado, parlayId, ParlaySeleccionInput, partidoId (+5 more)

### Community 77 - "auth_provider.dart"
Cohesion: 0.15
Nodes (12): ../../core/auth_storage.dart, autenticado, _autenticar, _cargando, _cargarSesion, _dataSource, _error, login (+4 more)

### Community 78 - "_necesita_actualizacion"
Cohesion: 0.32
Nodes (11): _necesita_actualizacion(), datetime, Lógica pura (sin DB) — separada para poder testearla sin que partidos reales de…, _partido(), datetime, La guardia de job_partidos_en_vivo decide si vale la pena gastar un request de…, test_partido_en_vivo_dispara_actualizacion(), test_partido_ns_con_hora_pasada_dispara_actualizacion() (+3 more)

### Community 79 - "job_odds.py"
Cohesion: 0.22
Nodes (7): _linea_a_clave(), _parsear_bookmaker(), _parsear_handicap(), _parsear_over_under(), Job de cuotas — trae odds reales de API-Football (gratis, por fixture_id) para…, 2.5' -> '2_5', '-1.5' -> 'm1_5', '+1.5' -> '1_5' (mismo formato que…, {"odds_local": 1.9, ...} de un bookmaker — solo mercados mapeados.

### Community 80 - "partido_remote_ds.dart"
Cohesion: 0.18
Nodes (10): _client, _get, getDetalle, _getList, getPrediccionesHoy, getPrediccionesMias, getRecomendadas, getStatsModelo (+2 more)

### Community 81 - "api_client.py"
Cohesion: 0.27
Nodes (6): _fecha_hoy(), get_estadisticas_equipo(), get_fixtures_hoy(), get_h2h(), get_standings(), main()

### Community 82 - "analisis_remote_ds.dart"
Cohesion: 0.25
Nodes (7): _client, _get, getJugadores, getKelly, getKellyPortafolio, guardarMercados, ../models/analisis_avanzado_model.dart

### Community 83 - "String?"
Cohesion: 0.25
Nodes (7): build, _fallback, nombre, size, TeamLogo, url, String?

### Community 84 - "analisis_repo_impl.dart"
Cohesion: 0.29
Nodes (6): ../../core/http/auth_client.dart, ../datasources/analisis_remote_ds.dart, ../../domain/repositories/analisis_repository.dart, AnalisisRemoteDataSource, create, _dataSource

### Community 85 - "analisis_imagen_model.dart"
Cohesion: 0.29
Nodes (6): ../../domain/entities/analisis_imagen.dart, AnalisisImagenResultadoModel, fromJson, SeleccionImagenModel, AnalisisImagenResultado, SeleccionImagen

### Community 86 - "../../domain/entities/parlay.dart"
Cohesion: 0.40
Nodes (4): ../../domain/entities/parlay.dart, fromJson, ParlayResultadoModel, ParlayResultado

## Knowledge Gaps
- **474 isolated node(s):** `Config`, `XCTest`, `AuthStorage`, `_claveToken`, `_storage` (+469 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_post` connect `predicciones.py` to `auth_remote_ds.dart`, `test_auth.py`?**
  _High betweenness centrality (0.411) - this node is a cross-community bridge._
- **Why does `guardar_mercados()` connect `predicciones.py` to `simular_partido`, `PrediccionRepository`, `PartidoRepository`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Why does `apuesta_combinada()` connect `predicciones.py` to `simular_partido`, `PartidoRepository`?**
  _High betweenness centrality (0.120) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `Partido` (e.g. with `Base` and `CodificadorTemporal`) actually correct?**
  _`Partido` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `PartidoRepository` (e.g. with `GuardarMercadosRequest` and `ParlayRequest`) actually correct?**
  _`PartidoRepository` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `PrediccionRepository` (e.g. with `GuardarMercadosRequest` and `ParlayRequest`) actually correct?**
  _`PrediccionRepository` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Config`, `XCTest`, `AuthStorage` to the rest of the system?**
  _474 weakly-connected nodes found - possible documentation gaps or missing edges._