# Graph Report - BetML_Pro  (2026-08-14)

## Corpus Check
- 200 files · ~286,708 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1886 nodes · 3563 edges · 113 communities (106 shown, 7 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 103 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d7f293f4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- tests/test_kelly.py
- test_auth.py
- presupuesto.py
- PartidoRepository
- PartidoRepository
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
- job_sofascore_en_vivo.py
- theme.dart
- detalle_screen.dart
- get
- constants.dart
- simular_partido
- State
- partidos_provider.dart
- simular_jugadores_partido
- database.py
- main.dart
- test_alineaciones.py
- orquestador.py
- manifest.json
- partido_model.dart
- analisis_avanzado_screen.dart
- analisis_avanzado.dart
- the_odds_api.py
- failures.dart
- recomendadas.dart
- router.dart
- parlay_screen.dart
- analisis_remote_ds.dart
- login_screen.dart
- ../../core/theme.dart
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
- job_crear_fixtures_sofascore.py
- design_system.dart
- BetML Pro — handoff operativo (2026-08-14)
- parlay.dart
- auth_provider.dart
- package:flutter/material.dart
- job_odds_en_vivo.py
- partido_remote_ds.dart
- pipeline/config.py
- stats_screen.dart
- test_sofascore_en_vivo.py
- partido_repo_impl.dart
- odds_api_io.py
- auth_storage.dart
- frontend
- LaunchImage.imageset/README.md
- bool?
- DateTime?
- auth_client.dart
- test_odds_en_vivo.py
- auth_remote_ds.dart
- Prediccion
- fusionar_equipos.py
- deploy_betml.py
- _Handler
- _parsear_evento
- test_calibracion_produccion.py
- migrar_bd.py
- test_mlops.py
- parsear_mercados
- job_cerrar_predicciones.py
- kelly_portfolio
- partidos.py
- encoger
- product_analytics.dart

## God Nodes (most connected - your core abstractions)
1. `Partido` - 49 edges
2. `PartidoRepository` - 38 edges
3. `PrediccionRepository` - 35 edges
4. `get()` - 31 edges
5. `SofascoreCliente` - 30 edges
6. `PrediccionService` - 30 edges
7. `crear_tablas()` - 29 edges
8. `Usuario` - 28 edges
9. `simular_partido()` - 26 edges
10. `Equipo` - 25 edges

## Surprising Connections (you probably didn't know these)
- `test_stats_por_mercado_no_mezcla_fuentes()` --calls--> `PrediccionRepository`  [EXTRACTED]
  tests/test_mlops.py → backend/repositories/prediccion_repo.py
- `test_parlay_guardado_pertenece_al_usuario()` --calls--> `SeleccionParlay`  [EXTRACTED]
  tests/test_seguridad_fase1.py → backend/api/routes/predicciones.py
- `test_parlay_guardado_pertenece_al_usuario()` --calls--> `ParlayRequest`  [EXTRACTED]
  tests/test_seguridad_fase1.py → backend/api/routes/predicciones.py
- `guardar_mercados()` --references--> `_post`  [EXTRACTED]
  backend/api/routes/predicciones.py → frontend/lib/data/datasources/auth_remote_ds.dart
- `apuesta_combinada()` --references--> `_post`  [EXTRACTED]
  backend/api/routes/predicciones.py → frontend/lib/data/datasources/auth_remote_ds.dart

## Import Cycles
- None detected.

## Communities (113 total, 7 thin omitted)

### Community 0 - "tests/test_kelly.py"
Cohesion: 0.12
Nodes (28): factor_confianza(), Cuánto confiar en la calibración de esta clase en este rango de probabilidad,…, analizar_mercados_kelly(), calcular_kelly(), construir_lista_mercados(), _expandir_over_under(), De un dict {'over_2_5':0.55,'under_2_5':0.45,...} arma tuplas (nombre_mercado,…, Analiza todos los mercados de un partido y calcula el stake óptimo para cada… (+20 more)

### Community 1 - "test_auth.py"
Cohesion: 0.06
Nodes (67): error_no_controlado(), Request, startup(), _emitir_tokens(), google(), GoogleRequest, login(), LoginRequest (+59 more)

### Community 2 - "presupuesto.py"
Cohesion: 0.26
Nodes (12): PresupuestoApiFootball, Contador de requests gastadas a API-Football por día — el plan free da 100/día,…, _hoy_utc(), Contador compartido de requests a API-Football por día — el plan free da…, Suma 1 al contador de hoy (crea la fila si hace falta). Devuelve el total usado…, registrar_uso(), restantes(), _limpiar() (+4 more)

### Community 3 - "PartidoRepository"
Cohesion: 0.13
Nodes (10): mercados_jugadores(), prediccion_ensemble(), predicciones_mias(), Predicción combinada — XGBoost + MLP + LSTM, votación ponderada por accuracy de…, Mercados individuales de jugador — tiros, tiros al arco, anotar, amarilla,…, Historial de predicciones guardadas por ESTE usuario (ver POST /{id}/guardar-…, PartidoRepository, date (+2 more)

### Community 4 - "PartidoRepository"
Cohesion: 0.11
Nodes (19): ../entities/partido.dart, ../entities/prediccion.dart, ../entities/recomendadas.dart, PartidoRepositoryImpl, PartidoRepository, GetDetallePartido, _repository, GetPartidosHoy (+11 more)

### Community 5 - "scheduler.py"
Cohesion: 0.07
Nodes (48): correr_backup(), Path, correr_job_estadisticas(), _necesita_actualizacion(), datetime, Lógica pura (sin DB) — separada para poder testearla sin que partidos reales de…, correr_orquestador_odds(), partidos_sin_cuotas() (+40 more)

### Community 6 - "job_reentrenar_modelos.py"
Cohesion: 0.11
Nodes (23): generar_dataset(), DataFrame, construir_grafo(), Construcción del grafo equipo-jugador para la GNN. Dos tipos de nodo (equipo,…, Devuelve (grafo, id_a_indice_equipo, id_a_indice_jugador). fecha_corte=None usa…, entrenar_modelo(), guardar_modelo(), DataFrame (+15 more)

### Community 7 - "ensemble.py"
Cohesion: 0.12
Nodes (27): ajustar_calibracion(), calibrar_probabilidades(), cargar_calibracion(), _cargar_calibracion_mtime(), guardar_calibracion(), ndarray, Path, Calibración de probabilidades del modelo — necesaria para que Kelly tenga… (+19 more)

### Community 8 - "PrediccionRepository"
Cohesion: 0.12
Nodes (13): PrediccionRepository, Prediccion, Session, Cierra TODAS las predicciones de un partido con el mismo resultado_real — solo…, Cierra UNA predicción puntual, ya resuelta externamente (ver…, usuario_id=None significa "la generó el sistema" — ver el docstring de…, usuario_id es OBLIGATORIO en la práctica para la pantalla de "Mis…, Session (+5 more)

### Community 9 - "lstm.py"
Cohesion: 0.11
Nodes (18): obtener_secuencia_equipo(), Últimos n partidos del equipo (local o visitante, cualquiera de los dos) antes…, cargar_lstm(), CodificadorTemporal, _DatasetSecuencias, entrenar_lstm(), guardar_lstm(), _pad_izquierda() (+10 more)

### Community 10 - "partido.dart"
Cohesion: 0.07
Nodes (27): enJuego, estado, fecha, fechaHoraLarga, golesLocal, golesVisit, hora, id (+19 more)

### Community 11 - "prediccion.dart"
Cohesion: 0.04
Nodes (50): double get, accuracy, accuracyStr, acertadas, acerto, agrupar, altaConfianza, clave (+42 more)

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
Cohesion: 0.12
Nodes (36): analizar_captura(), apuesta_combinada(), _correr_montecarlo_partido(), guardar_mercados(), GuardarMercadosRequest, kelly_partido(), kelly_portafolio_partido(), montecarlo_partido() (+28 more)

### Community 16 - "calculador.py"
Cohesion: 0.28
Nodes (12): calcular_forma(), calcular_h2h(), calcular_rating_jugadores(), calcular_stats_sofascore(), calcular_win_rate(), construir_features_partido(), Partido, Session (+4 more)

### Community 17 - "mlp.py"
Cohesion: 0.17
Nodes (12): cargar_mlp(), _DatasetMultiObjetivo, entrenar_mlp(), guardar_mlp(), _perdida_batch(), DataFrame, Dataset, Path (+4 more)

### Community 18 - "job_sofascore_en_vivo.py"
Cohesion: 0.10
Nodes (31): EstadisticaSofascore, Stats avanzadas del partido desde Sofascore. xG, presiones, duelos, pases…, main(), Ids de torneo ya aprendidos para esta liga., torneos_conocidos(), guardar_jugadores(), guardar_stats_sofascore(), Session (+23 more)

### Community 19 - "theme.dart"
Cohesion: 0.06
Nodes (36): AppColors get, BuildContext, Color bg, bg2,, Color brick,, Color ledger,, Color line,, Color pitch,, Color shadowDark, (+28 more)

### Community 20 - "detalle_screen.dart"
Cohesion: 0.04
Nodes (63): dart:async, ../../domain/usecases/get_detalle_partido.dart, ../../domain/usecases/get_prediccion_en_vivo.dart, double width,, _EquipoSeccion, _JugadoresTab, _JugadorRow, _MensajeError (+55 more)

### Community 21 - "get"
Cohesion: 0.18
Nodes (12): health(), root(), Session, Métricas de rendimiento del modelo — MLOps tracking. Incluye…, stats_modelo(), _fecha_hoy(), get(), get_estadisticas_equipo() (+4 more)

### Community 22 - "constants.dart"
Cohesion: 0.07
Nodes (29): analizarCaptura, ApiConstants, AppConstants, appName, appVersion, authGoogle, authLogin, authLogout (+21 more)

### Community 23 - "simular_partido"
Cohesion: 0.13
Nodes (26): cargar_rho(), _cargar_rho_mtime(), _grid_marcadores(), _handicap_asiatico(), ndarray, Simula un partido N veces muestreando de la distribución conjunta Poisson…, Hándicap asiático derivado de la diferencia de goles ya simulada (no consume…, Reparte los goles YA simulados del partido completo entre 1T/2T — cada gol,… (+18 more)

### Community 24 - "State"
Cohesion: 0.16
Nodes (18): AnalisisAvanzadoScreen, _AnalisisAvanzadoScreenState, _JugadorDetalleSheet, _JugadorDetalleSheetState, _MercadosTab, _MercadosTabState, DetalleScreen, _DetalleScreenState (+10 more)

### Community 25 - "partidos_provider.dart"
Cohesion: 0.07
Nodes (29): bool get, ../../data/repositories/partido_repo_impl.dart, ../../domain/usecases/get_partidos_hoy.dart, ../../domain/usecases/get_stats_modelo.dart, _cargando, cargarPartidosHoy, _error, _fecha (+21 more)

### Community 26 - "simular_jugadores_partido"
Cohesion: 0.29
Nodes (9): calcular_forma_jugador(), obtener_titulares_probables(), Session, Jugadores titulares en al menos min_apariciones (40% default) de los últimos…, Promedio de stats del jugador en sus últimos n partidos disputados antes de…, Simulación Monte Carlo de mercados individuales de jugador — tiros, tiros al…, Simula mercados individuales para el XI de ambos equipos. Usa la alineación…, simular_jugador() (+1 more)

### Community 27 - "database.py"
Cohesion: 0.20
Nodes (14): crear_tablas(), guardar_partido(), Session, Crea el equipo si no existe. Si ya existe pero le falta el logo (723 equipos ya…, _upsert_equipo(), correr_job_historico(), correr_job_temporada_actual(), _parsear_estadisticas() (+6 more)

### Community 28 - "main.dart"
Cohesion: 0.18
Nodes (11): core/router.dart, _auth, BetMLApp, _BetMLAppState, build, createState, main, _router (+3 more)

### Community 29 - "test_alineaciones.py"
Cohesion: 0.17
Nodes (17): Base, EstadisticaJugador, obtener_lineup_confirmada(), Features a nivel jugador — para los mercados individuales (tiros, tiros al…, XI real confirmado por Sofascore para ESTE partido (job_alineaciones.py lo trae…, _nombre_coincide(), Solo para casos claros (tests y uso puntual). El anclaje real usa…, DeclarativeBase (+9 more)

### Community 30 - "orquestador.py"
Cohesion: 0.17
Nodes (14): Odds, Cuotas reales de casas de apuestas — API-Football /odds (gratis por fixture_id,…, Lectura de cuotas guardadas por job_odds.py — mejor cuota disponible por…, correr_job_odds(), traer_cuotas(), _fuente_api_football(), _fuente_odds_api_io(), _fuente_sofascore() (+6 more)

### Community 31 - "manifest.json"
Cohesion: 0.18
Nodes (10): background_color, description, display, icons, name, orientation, prefer_related_applications, short_name (+2 more)

### Community 32 - "partido_model.dart"
Cohesion: 0.13
Nodes (14): ../../domain/entities/partido.dart, FactorModel, fromJson, MercadoModel, PartidoModel, PrediccionEnVivoModel, PrediccionGuardadaModel, PrediccionModel (+6 more)

### Community 33 - "analisis_avanzado_screen.dart"
Cohesion: 0.04
Nodes (49): ../../data/repositories/analisis_repo_impl.dart, ../../domain/usecases/get_jugadores_partido.dart, ../../domain/usecases/get_kelly_mercados.dart, ../../domain/usecases/get_kelly_portafolio.dart, ../../domain/usecases/guardar_mercados.dart, _abrirDetalle, _abrirDetalleJugador, _bloqueMercado (+41 more)

### Community 34 - "analisis_avanzado.dart"
Cohesion: 0.04
Nodes (48): asistenciasOverUnder, asistenciasPromedio, atajadasOverUnder, atajadasPromedio, clave, cuota, cuotaJusta, edge (+40 more)

### Community 35 - "the_odds_api.py"
Cohesion: 0.15
Nodes (16): _buscar_evento(), Cruza por nombres + fecha, con la misma similitud que el anclaje de Sofascore…, _buscar_partido(), Cuotas desde The Odds API (https://the-odds-api.com). Rinde mucho por llamada:…, Cruza por nombres de equipo + fecha cercana., Pide una vez por liga presente entre los partidos sin cuotas., _similitud(), traer_cuotas() (+8 more)

### Community 36 - "failures.dart"
Cohesion: 0.39
Nodes (7): Failure, mensaje, NetworkFailure, NotFoundFailure, ParseFailure, ServerFailure, statusCode

### Community 37 - "recomendadas.dart"
Cohesion: 0.05
Nodes (45): ../../domain/entities/recomendadas.dart, ApuestaIndividualModel, CombinadaMismoPartidoModel, fromJson, MercadoCombinadaModel, ParlaySugeridoModel, PataParlayModel, RecomendadasModel (+37 more)

### Community 38 - "router.dart"
Cohesion: 0.15
Nodes (12): buildRouter, presentation/providers/auth_provider.dart, ../presentation/screens/analisis_avanzado_screen.dart, ../presentation/screens/analizar_captura_screen.dart, ../presentation/screens/detalle_screen.dart, ../presentation/screens/home_screen.dart, ../presentation/screens/login_screen.dart, ../presentation/screens/mis_predicciones_screen.dart (+4 more)

### Community 39 - "parlay_screen.dart"
Cohesion: 0.08
Nodes (27): ../../data/datasources/parlay_remote_ds.dart, PartidosProvider, build, initState, build, _calculando, _calcular, createState (+19 more)

### Community 40 - "analisis_remote_ds.dart"
Cohesion: 0.12
Nodes (19): Client, ../../core/constants.dart, dart:convert, AnalisisImagenRemoteDataSource, analizar, _client, _client, _get (+11 more)

### Community 41 - "login_screen.dart"
Cohesion: 0.11
Nodes (21): Color?, AuthProvider, _beneficio, build, _campo, createState, dispose, _emailCtrl (+13 more)

### Community 42 - "../../core/theme.dart"
Cohesion: 0.22
Nodes (8): ../../core/theme.dart, dart:math, build, ConfidenceDial, ConfidenceMeter, label, size, value

### Community 44 - "modelos.py"
Cohesion: 0.19
Nodes (10): Equipo, EstadisticaPartido, Liga, Partido, _parsear_estadisticas(), _crear_schema_si_falta(), Aísla la suite de la base de PRODUCCIÓN. El `.env` de desarrollo apunta a la…, `create_all` crea tablas, no el schema que las contiene. (+2 more)

### Community 49 - "mis_predicciones_screen.dart"
Cohesion: 0.08
Nodes (23): ../../domain/usecases/get_predicciones_mias.dart, PrediccionesDePartido, actual, build, _cargando, _cargar, createState, _error (+15 more)

### Community 53 - "recomendadas_screen.dart"
Cohesion: 0.08
Nodes (24): ../../domain/usecases/get_recomendadas.dart, build, _cargando, _cargar, color, _CombinadasTab, createState, _dato (+16 more)

### Community 56 - "BetML_Pro_Informe_Tecnico_v3.md"
Cohesion: 0.11
Nodes (18): **1. Estado Actual del Proyecto**, **2.1 Fuente 1 — API-Football**, **2.2 Fuente 2 — Sofascore (Playwright)**, **2.3 Mapeo y Cruce de Fuentes**, **2. Pipeline ETL Dual — API-Football + Sofascore**, **3. Feature Engineering — 36 Variables del Modelo**, **4.1 Modelos de Gradient Boosting (XGBoost + LightGBM)**, **4.2 Red Neuronal MLP — Modelo Multiobjetivo** (+10 more)

### Community 57 - "../../core/errors/failures.dart"
Cohesion: 0.18
Nodes (13): ../../core/errors/failures.dart, ../entities/analisis_avanzado.dart, AnalisisRepositoryImpl, AnalisisRepository, GetJugadoresPartido, _repository, GetKellyMercados, _repository (+5 more)

### Community 58 - "analizar_captura_screen.dart"
Cohesion: 0.06
Nodes (37): ../../data/datasources/analisis_imagen_remote_ds.dart, ../../domain/entities/analisis_imagen.dart, double?, AnalisisImagenResultadoModel, fromJson, SeleccionImagenModel, AnalisisImagenResultado, aviso (+29 more)

### Community 61 - "job_alineaciones.py"
Cohesion: 0.13
Nodes (21): LigaSofascoreTorneo, Ids de torneo de Sofascore aprendidos para una liga nuestra. Una liga nuestra…, filtrar_candidatos(), _parecido(), Encuentra el id de torneo de Sofascore de una liga nuestra cuando…, True si comparten alguna palabra significativa (por raíz, para que 'Friendlies'…, [(torneo_id, nombre)] de TODOS los torneos con partidos ese día. La lista es la…, De la lista del día, los que se parecen por nombre a nuestra liga. Sin… (+13 more)

### Community 64 - ".predecir"
Cohesion: 0.14
Nodes (15): generar_resumen(), generar_resumen_h2h(), Por qué el modelo predijo lo que predijo — sin llamar a un LLM en cada request…, estimar_fraccion_restante(), Fracción del partido que falta jugar (0-1), para escalar el xG pre-partido en…, Partido, Recalcula 1X2 y mercados de gol EN VIVO dado el marcador y minuto actuales — no…, Genera lista de mercados recomendados según las probabilidades del modelo. Solo… (+7 more)

### Community 71 - "PartidoService"
Cohesion: 0.23
Nodes (9): PartidoService, Session, Lógica de negocio relacionada a partidos. Ensambla los datos de múltiples…, Convierte un objeto Partido en dict con datos relacionados. con_prediccion=True…, con_prediccion era un parámetro muerto (bug real encontrado en sesión:…, test_get_detalle_incluye_nombres_reales_no_ids(), test_get_detalle_partido_inexistente_devuelve_none(), test_get_partidos_hoy_cada_fila_trae_clave_prediccion() (+1 more)

### Community 72 - "analisis_avanzado_model.dart"
Cohesion: 0.13
Nodes (14): ../../domain/entities/analisis_avanzado.dart, fromJson, JugadoresPartidoModel, JugadorMercadoModel, KellyAnalisisModel, KellyMercadoModel, KellyPortafolioModel, MercadoPortafolioModel (+6 more)

### Community 73 - "job_crear_fixtures_sofascore.py"
Cohesion: 0.15
Nodes (17): anclar_si_corresponde(), buscar_candidatos(), equipos_de_la_liga(), Resolución de equipos/liga por nombre de Sofascore contra la BD propia.…, Una vez confirmado (por cruce con Partido: rival+fecha) cuál candidato era el…, id en NUESTRA BD de una liga por nombre (distinto del id de Sofascore usado…, Query base de equipos, acotada a los que ya jugaron en esta liga (evita que la…, Devuelve [(Equipo, score), ...]. score=None si vino de un sofascore_id ya… (+9 more)

### Community 74 - "design_system.dart"
Cohesion: 0.06
Nodes (36): EdgeInsets, build, child, ClayButton, ClayContainer, icon, label, loading (+28 more)

### Community 75 - "BetML Pro — handoff operativo (2026-08-14)"
Cohesion: 0.14
Nodes (13): 10. Rediseño UX/UI móvil, 11. Pendientes priorizados, 12. Prompt para retomar, 1. Estado actual, 2. Producción y despliegue, 3. Red de seguridad y pruebas, 4. Autenticación y seguridad, 5. Rendimiento medido (+5 more)

### Community 76 - "parlay.dart"
Cohesion: 0.11
Nodes (17): ../../domain/entities/parlay.dart, fromJson, ParlayResultadoModel, bankroll, cuotaCombinada, esValueBet, ev, mercado (+9 more)

### Community 77 - "auth_provider.dart"
Cohesion: 0.12
Nodes (15): ../../core/auth_storage.dart, ../../data/datasources/auth_remote_ds.dart, autenticado, _autenticar, _cargando, _cargarSesion, _dataSource, _error (+7 more)

### Community 78 - "package:flutter/material.dart"
Cohesion: 0.11
Nodes (16): AppBottomNav, AppTab, build, current, _destinos, main, _noop, package:flutter/material.dart (+8 more)

### Community 79 - "job_odds_en_vivo.py"
Cohesion: 0.15
Nodes (16): correr_job_odds_en_vivo(), _hay_partidos_en_vivo(), Job de cuotas EN VIVO — GET /odds/live (gratis en el plan actual, verificado en…, _linea_a_clave(), _parsear_bookmaker(), _parsear_btts(), _parsear_handicap(), _parsear_match_winner() (+8 more)

### Community 80 - "partido_remote_ds.dart"
Cohesion: 0.17
Nodes (11): _client, _get, getDetalle, _getList, getPrediccionEnVivo, getPrediccionesHoy, getPrediccionesMias, getRecomendadas (+3 more)

### Community 81 - "pipeline/config.py"
Cohesion: 0.15
Nodes (21): CacheJson, ahora_partidos(), fecha_hoy_partidos(), date, datetime, rango_utc_dia_partidos(), Ahora" en la misma referencia que Partido.fecha, para poder compararlos.…, Día futbolístico actual en Ecuador, independiente del TZ del proceso. (+13 more)

### Community 82 - "stats_screen.dart"
Cohesion: 0.13
Nodes (17): ChangeNotifier, ../../core/product_analytics.dart, StatsProvider, build, c, color, createState, initState (+9 more)

### Community 83 - "test_sofascore_en_vivo.py"
Cohesion: 0.23
Nodes (12): _estado_desde_evento(), _goles_desde(), _minuto_desde_evento(), Goles del TIEMPO REGLAMENTARIO. Ojo con "current": en un partido definido por…, Minuto en curso, derivado de cuándo arrancó el período actual — Sofascore no…, Traducción de un evento de Sofascore a nuestro modelo — lógica pura, sin DB ni…, test_estado_en_juego_sin_descripcion_no_inventa_periodo(), test_estado_en_juego_usa_la_descripcion_del_periodo() (+4 more)

### Community 84 - "partido_repo_impl.dart"
Cohesion: 0.14
Nodes (12): ../../core/http/auth_client.dart, ../datasources/analisis_remote_ds.dart, ../datasources/partido_remote_ds.dart, ../../domain/entities/prediccion.dart, ../../domain/repositories/analisis_repository.dart, ../../domain/repositories/partido_repository.dart, AnalisisRemoteDataSource, PartidoRemoteDataSource (+4 more)

### Community 85 - "odds_api_io.py"
Cohesion: 0.26
Nodes (12): _decimal(), _linea(), parsear_bookmakers(), Cuotas desde odds-api.io. Cobertura enorme (~4600 partidos no jugados en una…, 0.5 -> '0_5', -1.25 -> 'm1_25' (mismo formato que el resto)., A las claves odds_* de kelly.py, respetando el orden de CASAS., Parser de odds-api.io — datos calcados de la respuesta real para Tobol Kostanay…, test_betano_manda_sobre_bet365_en_el_mismo_mercado() (+4 more)

### Community 86 - "auth_storage.dart"
Cohesion: 0.18
Nodes (10): AuthStorage, borrarTokens, _claveAccess, _claveRefresh, guardarTokens, leerRefresh, leerToken, _storage (+2 more)

### Community 95 - "auth_client.dart"
Cohesion: 0.17
Nodes (11): ../auth_storage.dart, ../constants.dart, dart:typed_data, AuthClient, _enviarCopia, _inner, _refreshEnCurso, _renovar (+3 more)

### Community 96 - "test_odds_en_vivo.py"
Cohesion: 0.31
Nodes (6): _parsear_over_under_vivo(), _sin_suspender(), Parsers puros del feed /odds/live — sin DB, sin red. Cubre: filtro de mercados…, test_over_under_vivo_arma_clave_desde_handicap(), test_over_under_vivo_descarta_suspendidos(), test_sin_suspender_filtra_y_devuelve_value_odd()

### Community 97 - "auth_remote_ds.dart"
Cohesion: 0.20
Nodes (9): access, AuthRemoteDataSource, AuthTokens, _client, google, login, me, refresh (+1 more)

### Community 98 - "Prediccion"
Cohesion: 0.32
Nodes (6): Prediccion, Una predicción guardada para seguimiento. usuario_id NULL = la generó el…, correr_job_guardar_recomendadas(), Guarda las apuestas recomendadas del día para que se cierren solas contra el…, Solo mira las del SISTEMA (usuario_id NULL). Si mirara todas, que un usuario…, _ya_guardada()

### Community 99 - "fusionar_equipos.py"
Cohesion: 0.39
Nodes (7): correr_fusion(), encontrar_duplicados(), fusionar(), _normalizar(), _partidos_de(), Fusiona filas duplicadas del mismo equipo. Un club terminaba cargado dos veces…, [(sobreviviente, [a_fusionar...])] por nombre normalizado.

### Community 100 - "deploy_betml.py"
Cohesion: 0.47
Nodes (5): archivos_a_subir(), main(), mkdir_p(), Sube BetML Pro al servidor y reconstruye los contenedores. Mismo patrón que el…, Crea los directorios que falten, pero SOLO por debajo de REMOTO. Recorrer desde…

### Community 101 - "_Handler"
Cohesion: 0.40
Nodes (3): _Handler, main(), Túnel SSH a la base de producción, para desarrollar en local contra los datos…

### Community 102 - "_parsear_evento"
Cohesion: 0.36
Nodes (8): _decimal(), _parsear_evento(), Del JSON de un evento a las claves odds_* que usa kelly.py. Se queda con la…, Parser de The Odds API — datos con la forma exacta que documenta su guia v4…, test_decimal_descarta_valores_imposibles(), test_h2h_asigna_local_visitante_por_nombre_no_por_orden(), test_se_queda_con_la_mejor_cuota_entre_bookmakers(), test_totals_usa_el_campo_point_como_linea()

### Community 103 - "test_calibracion_produccion.py"
Cohesion: 0.13
Nodes (22): ajustar_desde_predicciones(), calcular_factor(), cargar(), corregir(), familia_de(), El sistema aprende de sus propios errores, por tipo de mercado. La idea, en…, Calcula un factor de corrección por familia de mercado. Mira TODAS las…, Aplica lo aprendido. Sin datos de esa familia devuelve la probabilidad tal cual… (+14 more)

### Community 104 - "migrar_bd.py"
Cohesion: 0.50
Nodes (3): _db_url_local(), dump_local(), Copia la base local al Postgres de producción (una sola vez, para arrancar con…

### Community 105 - "test_mlops.py"
Cohesion: 0.11
Nodes (21): Parlay, ParlaySeleccion, Apuesta combinada guardada — ver /predicciones/combinada. acerto=None mientras…, Una pata de un Parlay — mercado usa la misma convención de clave interna que…, db(), _fixture(), Payload de API-Football con lo mínimo que lee guardar_partido., _crear_cerradas() (+13 more)

### Community 106 - "parsear_mercados"
Cohesion: 0.23
Nodes (12): _a_decimal(), _linea_a_clave(), parsear_mercados(), 1/5" -> 1.20, "19/4" -> 5.75, "9/1" -> 10.0, 2.5' -> '2_5', '-1.5' -> 'm1_5' (mismo formato que montecarlo.py y job_odds.py,…, De la respuesta de Sofascore a las claves odds_* que usa kelly.py., Parser de cuotas de Sofascore — datos calcados de la respuesta real de…, test_convierte_cuota_fraccionaria_a_decimal() (+4 more)

### Community 107 - "job_cerrar_predicciones.py"
Cohesion: 0.18
Nodes (15): Partido, Resuelve si una selección de cualquier mercado ganó o perdió, dado el resultado…, True si la selección ganó, False si perdió, None si no se puede resolver…, resolver_mercado(), _resultado_1x2(), _stats(), _cerrar_parlays_pendientes(), _cerrar_predicciones_individuales() (+7 more)

### Community 108 - "kelly_portfolio"
Cohesion: 0.25
Nodes (7): kelly_portfolio(), probabilidad_ruina(), Kelly de portafolio — para cuando se apuesta a VARIOS mercados del MISMO…, mercados: [{"nombre": str, "gana_escenario": np.ndarray[bool] (n,), "cuota":…, Simula qué pasa si esta MISMA combinación de apuestas (mismos stakes) se repite…, test_kelly_portfolio_correlacionado_no_excede_suma_ingenua(), test_probabilidad_ruina_escala_con_el_stake()

### Community 109 - "partidos.py"
Cohesion: 0.53
Nodes (5): detalle_partido(), partidos_hoy(), partidos_liga(), prediccion_partido(), Session

### Community 110 - "encoger"
Cohesion: 0.50
Nodes (3): encoger(), Medias globales de córners/tarjetas y encogimiento hacia ellas. Por qué existe:…, Mezcla el promedio del equipo con la media global. Sin muestra devuelve la…

### Community 112 - "product_analytics.dart"
Cohesion: 0.50
Nodes (3): ProductAnalytics, track, package:flutter/foundation.dart

## Knowledge Gaps
- **548 isolated node(s):** `Config`, `XCTest`, `AuthStorage`, `_claveAccess`, `_claveRefresh` (+543 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_post` connect `test_auth.py` to `auth_remote_ds.dart`, `predicciones.py`?**
  _High betweenness centrality (0.425) - this node is a cross-community bridge._
- **Why does `guardar_mercados()` connect `predicciones.py` to `tests/test_kelly.py`, `test_auth.py`, `PartidoRepository`, `PrediccionRepository`?**
  _High betweenness centrality (0.126) - this node is a cross-community bridge._
- **Why does `apuesta_combinada()` connect `predicciones.py` to `tests/test_kelly.py`, `test_mlops.py`, `PartidoRepository`, `test_auth.py`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `Partido` (e.g. with `Base` and `CodificadorTemporal`) actually correct?**
  _`Partido` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `PartidoRepository` (e.g. with `GuardarMercadosRequest` and `ParlayRequest`) actually correct?**
  _`PartidoRepository` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `PrediccionRepository` (e.g. with `GuardarMercadosRequest` and `ParlayRequest`) actually correct?**
  _`PrediccionRepository` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Config`, `XCTest`, `AuthStorage` to the rest of the system?**
  _548 weakly-connected nodes found - possible documentation gaps or missing edges._