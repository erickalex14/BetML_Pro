# Graph Report - BetML_Pro  (2026-08-17)

## Corpus Check
- 223 files · ~297,592 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2097 nodes · 4001 edges · 131 communities (120 shown, 11 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 109 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d7f293f4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- tests/test_kelly.py
- test_auth.py
- get
- PartidoRepository
- ../../core/errors/failures.dart
- scheduler.py
- ensemble.py
- calibracion.py
- PrediccionRepository
- lstm.py
- partido.dart
- prediccion.dart
- AppDelegate
- test_parser_imagen.py
- SofascoreCliente
- analizar_captura
- construir_features_partido
- job_reentrenar_modelos.py
- job_sofascore_en_vivo.py
- theme.dart
- StatelessWidget
- database.py
- constants.dart
- simular_partido
- detalle_screen.dart
- partidos_provider.dart
- simular_jugadores_partido
- Partido
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
- package:go_router/go_router.dart
- parlay_screen.dart
- analisis_remote_ds.dart
- login_screen.dart
- package:flutter/material.dart
- FlutterActivity
- Equipo
- mis_predicciones_screen.dart
- recomendadas_screen.dart
- BetML_Pro_Informe_Tecnico_v3.md
- AnalisisRepository
- analizar_captura_screen.dart
- job_alineaciones.py
- generar_resumen
- Partido
- Prediccion
- PartidoService
- analisis_avanzado_model.dart
- crear_tablas
- design_system.dart
- BetML Pro — handoff operativo (2026-08-14)
- parlay.dart
- auth_provider.dart
- widget_test.dart
- api_client.py
- partido_remote_ds.dart
- fecha_hoy_partidos
- stats_screen.dart
- test_sofascore_en_vivo.py
- backtest_walk_forward.py
- odds_api_io.py
- PrediccionService
- frontend
- LaunchImage.imageset/README.md
- bool?
- DateTime?
- auth_client.dart
- division_temporal
- analisis_imagen.dart
- predicciones_recomendadas
- modelos.py
- ejecutar
- _Handler
- timedelta
- test_calibracion_produccion.py
- migrar_bd.py
- test_guardador_no_regresa.py
- job_odds_sofascore.py
- resolver_mercado.py
- prediccion_service.py
- analizar_mercados_kelly
- analisis_imagen_model.dart
- prediction_coupon_provider.dart
- recomendadas_model.dart
- clay.dart
- String?
- Odds
- auth_storage.dart
- auth_remote_ds.dart
- partido_service.py
- parser.py
- auditar_rendimiento_prod.py
- fusionar_equipos.py
- analisis_repo_impl.dart
- correr_job_alineaciones
- descargar_dataset_prod.py
- Q: Why does _post connect test_auth.py to auth_remote_ds.dart and predicciones.py?
- auditar_historial_prod.py
- ejecutar_odds_prod.py
- corregir_sofascore_id_prod.py
- PronosticoJugadorModel

## God Nodes (most connected - your core abstractions)
1. `Partido` - 54 edges
2. `PartidoRepository` - 38 edges
3. `PrediccionRepository` - 35 edges
4. `PrediccionService` - 33 edges
5. `get()` - 31 edges
6. `SofascoreCliente` - 30 edges
7. `crear_tablas()` - 29 edges
8. `Usuario` - 28 edges
9. `Equipo` - 27 edges
10. `simular_partido()` - 26 edges

## Surprising Connections (you probably didn't know these)
- `test_aplana_mercado_jugador_con_clave_estable()` --calls--> `mercados_jugadores_calculados()`  [EXTRACTED]
  tests/test_mercados_jugadores.py → backend/models/jugadores_montecarlo.py
- `test_backup_invalido_no_borra_el_anterior()` --indirect_call--> `ejecutar()`  [INFERRED]
  tests/test_backup.py → deploy/deploy_apk.py
- `test_token_invalido_rechazado()` --calls--> `verificar_token()`  [EXTRACTED]
  tests/test_auth.py → backend/core/auth.py
- `_equipo_temporal()` --calls--> `Equipo`  [EXTRACTED]
  tests/test_alineaciones.py → backend/db/modelos.py
- `test_fallback_general_cubre_muestra_de_localia_sin_fuga_temporal()` --calls--> `Equipo`  [EXTRACTED]
  tests/test_calidad_historial.py → backend/db/modelos.py

## Import Cycles
- None detected.

## Communities (131 total, 11 thin omitted)

### Community 0 - "tests/test_kelly.py"
Cohesion: 0.14
Nodes (22): calcular_kelly(), kelly_portfolio(), probabilidad_ruina(), Kelly de portafolio — para cuando se apuesta a VARIOS mercados del MISMO…, mercados: [{"nombre": str, "gana_escenario": np.ndarray[bool] (n,), "cuota":…, Simula qué pasa si esta MISMA combinación de apuestas (mismos stakes) se repite…, Calcula el stake óptimo usando el Criterio de Kelly Fraccionario. Parámetros:…, calcular_parlay_kelly() (+14 more)

### Community 1 - "test_auth.py"
Cohesion: 0.07
Nodes (55): _emitir_tokens(), google(), GoogleRequest, login(), LoginRequest, logout(), BaseModel, limit (+47 more)

### Community 2 - "get"
Cohesion: 0.14
Nodes (21): health(), root(), me(), detalle_partido(), partidos_hoy(), partidos_liga(), prediccion_partido(), Session (+13 more)

### Community 3 - "PartidoRepository"
Cohesion: 0.21
Nodes (4): PartidoRepository, date, Partido, Session

### Community 4 - "../../core/errors/failures.dart"
Cohesion: 0.12
Nodes (20): ../../core/errors/failures.dart, ../entities/partido.dart, ../entities/prediccion.dart, ../entities/recomendadas.dart, PartidoRepositoryImpl, PartidoRepository, GetDetallePartido, _repository (+12 more)

### Community 5 - "scheduler.py"
Cohesion: 0.13
Nodes (21): correr_backup(), Path, iniciar_scheduler(), job_backup(), job_cerrar_predicciones(), job_estadisticas(), job_guardar_recomendadas(), job_odds_cascada() (+13 more)

### Community 6 - "ensemble.py"
Cohesion: 0.11
Nodes (23): construir_grafo(), Construcción del grafo equipo-jugador para la GNN. Dos tipos de nodo (equipo,…, Devuelve (grafo, id_a_indice_equipo, id_a_indice_jugador). fecha_corte=None usa…, predecir_ensemble(), Partido, Ensemble — combina XGBoost, MLP, LSTM y GNN por votación ponderada. El peso de…, persistir=True guarda la predicción para tracking de MLOps (ver…, cargar_metricas_xgboost() (+15 more)

### Community 7 - "calibracion.py"
Cohesion: 0.17
Nodes (16): calibrar_probabilidades(), cargar_calibracion(), _cargar_calibracion_mtime(), guardar_calibracion(), ndarray, Path, Calibración de probabilidades del modelo — necesaria para que Kelly tenga…, Aplica el calibrador de cada clase y renormaliza a que sume 1. (+8 more)

### Community 8 - "PrediccionRepository"
Cohesion: 0.07
Nodes (34): _peso_desde_brier(), _peso_modelo(), Session, 0.5 representa el Brier neutral 0.25; acota modelos extremos., _cerrar_parlays_pendientes(), _cerrar_predicciones_individuales(), _clave_mercado(), correr_job_cerrar_predicciones() (+26 more)

### Community 9 - "lstm.py"
Cohesion: 0.11
Nodes (18): obtener_secuencia_equipo(), Últimos n partidos del equipo (local o visitante, cualquiera de los dos) antes…, cargar_lstm(), CodificadorTemporal, _DatasetSecuencias, entrenar_lstm(), guardar_lstm(), _pad_izquierda() (+10 more)

### Community 10 - "partido.dart"
Cohesion: 0.06
Nodes (33): calidad, codigo, enJuego, estado, fecha, fechaHoraLarga, golesLocal, golesVisit (+25 more)

### Community 11 - "prediccion.dart"
Cohesion: 0.04
Nodes (50): double get, accuracy, accuracyStr, acertadas, acerto, agrupar, altaConfianza, calidadDatos (+42 more)

### Community 12 - "AppDelegate"
Cohesion: 0.11
Nodes (14): Any, Flutter, FlutterAppDelegate, FlutterImplicitEngineBridge, FlutterImplicitEngineDelegate, FlutterSceneDelegate, AppDelegate, Bool (+6 more)

### Community 13 - "test_parser_imagen.py"
Cohesion: 0.16
Nodes (20): analizar_captura_parley(), _clasificar_over_under(), _detectar_categoria(), _es_btts(), _es_resultado_partido(), extraer_texto(), _get_lector(), _linea_a_clave() (+12 more)

### Community 14 - "SofascoreCliente"
Cohesion: 0.09
Nodes (15): Cliente de Sofascore usando Playwright. Lanza un browser Chromium real para…, Arranca el browser y visita Sofascore para obtener cookies., Cierra el browser limpiamente., Hace una request a la API de Sofascore usando el browser. Navega directamente a…, Trae todos los partidos de fútbol de una fecha., Trae estadísticas completas de un partido., Trae alineaciones y stats de jugadores., Trae partidos históricos (ya jugados) de una liga y temporada — /events/last/,… (+7 more)

### Community 15 - "analizar_captura"
Cohesion: 0.15
Nodes (16): analizar_captura(), guardar_mercados(), kelly_partido(), kelly_portafolio_partido(), limit, post, Request, Calcula el stake óptimo con Kelly Criterion para un partido. guardar=True… (+8 more)

### Community 16 - "construir_features_partido"
Cohesion: 0.24
Nodes (17): calcular_forma(), calcular_forma_general(), calcular_h2h(), calcular_rating_jugadores(), calcular_stats_sofascore(), calcular_win_rate(), construir_features_partido(), diagnosticar_historial() (+9 more)

### Community 17 - "job_reentrenar_modelos.py"
Cohesion: 0.12
Nodes (22): generar_dataset(), DataFrame, ajustar_calibracion(), entrenar_modelo(), guardar_modelo(), DataFrame, cargar_mlp(), _DatasetMultiObjetivo (+14 more)

### Community 18 - "job_sofascore_en_vivo.py"
Cohesion: 0.14
Nodes (17): EstadisticaSofascore, Stats avanzadas del partido desde Sofascore. xG, presiones, duelos, pases…, Ids de torneo ya aprendidos para esta liga., torneos_conocidos(), guardar_jugadores(), guardar_stats_sofascore(), Session, Guarda estadísticas de Sofascore en BD — upsert por partido_id. Antes saltaba… (+9 more)

### Community 19 - "theme.dart"
Cohesion: 0.06
Nodes (34): AppColors get, BuildContext, Color bg, bg2,, Color brick,, Color ledger,, Color line,, Color pitch,, Color shadowDark, (+26 more)

### Community 20 - "StatelessWidget"
Cohesion: 0.05
Nodes (43): double width,, _EquipoSeccion, _JugadoresTab, _JugadorRow, _MensajeError, _MercadoKellyRow, _MercadosPorCategoria, _Metric (+35 more)

### Community 21 - "database.py"
Cohesion: 0.15
Nodes (13): error_no_controlado(), Request, startup(), Session, Métricas de rendimiento del modelo — MLOps tracking. Incluye…, stats_modelo(), Dependencias de FastAPI para proteger rutas con JWT. Uso: agregar `usuario:…, get_db() (+5 more)

### Community 22 - "constants.dart"
Cohesion: 0.07
Nodes (29): analizarCaptura, ApiConstants, AppConstants, appName, appVersion, authGoogle, authLogin, authLogout (+21 more)

### Community 23 - "simular_partido"
Cohesion: 0.12
Nodes (27): cargar_rho(), _cargar_rho_mtime(), _grid_marcadores(), _handicap_asiatico(), ndarray, Simula un partido N veces muestreando de la distribución conjunta Poisson…, Hándicap asiático derivado de la diferencia de goles ya simulada (no consume…, Reparte los goles YA simulados del partido completo entre 1T/2T — cada gol,… (+19 more)

### Community 24 - "detalle_screen.dart"
Cohesion: 0.07
Nodes (30): dart:async, ../../domain/usecases/get_detalle_partido.dart, ../../domain/usecases/get_prediccion_en_vivo.dart, _autoRefresh, _cargando, _cargar, child, _Contenido (+22 more)

### Community 25 - "partidos_provider.dart"
Cohesion: 0.09
Nodes (23): bool get, ../../data/repositories/partido_repo_impl.dart, ../../domain/usecases/get_partidos_hoy.dart, ../../domain/usecases/get_stats_modelo.dart, _cargando, cargarPartidosHoy, _error, _fecha (+15 more)

### Community 26 - "simular_jugadores_partido"
Cohesion: 0.23
Nodes (11): calcular_forma_jugador(), obtener_titulares_probables(), Session, Jugadores titulares en al menos min_apariciones (40% default) de los últimos…, Promedio de stats del jugador en sus últimos n partidos disputados antes de…, clave_mercado_jugador(), Simulación Monte Carlo de mercados individuales de jugador — tiros, tiros al…, Simula mercados individuales para el XI de ambos equipos. Usa la alineación… (+3 more)

### Community 27 - "Partido"
Cohesion: 0.21
Nodes (11): EstadisticaPartido, Partido, guardar_partido(), Session, Crea el equipo si no existe. Si ya existe pero le falta el logo (723 equipos ya…, _upsert_equipo(), correr_job_estadisticas(), _parsear_estadisticas() (+3 more)

### Community 28 - "main.dart"
Cohesion: 0.08
Nodes (24): core/router.dart, buildRouter, _auth, BetMLApp, _BetMLAppState, build, createState, main (+16 more)

### Community 29 - "test_alineaciones.py"
Cohesion: 0.16
Nodes (20): EstadisticaJugador, obtener_lineup_confirmada(), Features a nivel jugador — para los mercados individuales (tiros, tiros al…, XI real confirmado por Sofascore para ESTE partido (job_alineaciones.py lo trae…, ahora_partidos(), Ahora" en la misma referencia que Partido.fecha, para poder compararlos.…, _nombre_coincide(), _partidos_a_anclar() (+12 more)

### Community 30 - "orquestador.py"
Cohesion: 0.21
Nodes (12): correr_job_odds(), _buscar_evento(), Cruza por nombres + fecha, con la misma similitud que el anclaje de Sofascore…, traer_cuotas(), correr_orquestador_odds(), diagnosticar_cobertura(), _fuente_api_football(), _fuente_odds_api_io() (+4 more)

### Community 31 - "manifest.json"
Cohesion: 0.18
Nodes (10): background_color, description, display, icons, name, orientation, prefer_related_applications, short_name (+2 more)

### Community 32 - "partido_model.dart"
Cohesion: 0.09
Nodes (22): ../datasources/partido_remote_ds.dart, ../../domain/entities/partido.dart, ../../domain/entities/prediccion.dart, ../../domain/repositories/partido_repository.dart, PartidoRemoteDataSource, DisponibilidadPrediccionModel, FactorModel, fromJson (+14 more)

### Community 33 - "analisis_avanzado_screen.dart"
Cohesion: 0.04
Nodes (58): ../../domain/usecases/get_jugadores_partido.dart, ../../domain/usecases/get_kelly_portafolio.dart, ../../domain/usecases/guardar_mercados.dart, _abrirDetalle, _abrirDetalleJugador, AnalisisAvanzadoScreen, _AnalisisAvanzadoScreenState, _bloqueMercado (+50 more)

### Community 34 - "analisis_avanzado.dart"
Cohesion: 0.04
Nodes (50): asistenciasOverUnder, asistenciasPromedio, atajadasOverUnder, atajadasPromedio, clave, cuota, cuotaJusta, edge (+42 more)

### Community 35 - "the_odds_api.py"
Cohesion: 0.13
Nodes (22): _buscar_partido(), _decimal(), _parsear_evento(), Cuotas desde The Odds API (https://the-odds-api.com). Rinde mucho por llamada:…, Cruza por nombres de equipo + fecha cercana., Pide una vez por liga presente entre los partidos sin cuotas., Del JSON de un evento a las claves odds_* que usa kelly.py. Se queda con la…, _similitud() (+14 more)

### Community 36 - "failures.dart"
Cohesion: 0.39
Nodes (7): Failure, mensaje, NetworkFailure, NotFoundFailure, ParseFailure, ServerFailure, statusCode

### Community 37 - "recomendadas.dart"
Cohesion: 0.05
Nodes (40): acerto, clave, combinadasFijas, combinadasSonadoras, cuota, cuotaCombinada, edge, enJuego (+32 more)

### Community 38 - "package:go_router/go_router.dart"
Cohesion: 0.25
Nodes (7): AppBottomNav, AppTab, build, current, _destinos, package:go_router/go_router.dart, prediction_coupon.dart

### Community 39 - "parlay_screen.dart"
Cohesion: 0.04
Nodes (57): ../../data/datasources/parlay_remote_ds.dart, ../../data/repositories/analisis_repo_impl.dart, ../../domain/entities/parlay.dart, ../../domain/usecases/get_kelly_mercados.dart, fromJson, ParlayResultadoModel, ParlayResultado, PartidosProvider (+49 more)

### Community 40 - "analisis_remote_ds.dart"
Cohesion: 0.12
Nodes (19): Client, ../../core/constants.dart, dart:convert, AnalisisImagenRemoteDataSource, analizar, _client, _client, _get (+11 more)

### Community 41 - "login_screen.dart"
Cohesion: 0.14
Nodes (14): Color?, _beneficio, build, _campo, createState, dispose, _emailCtrl, LoginScreen (+6 more)

### Community 42 - "package:flutter/material.dart"
Cohesion: 0.12
Nodes (15): ../../core/theme.dart, dart:math, build, ConfidenceDial, ConfidenceMeter, label, size, value (+7 more)

### Community 44 - "Equipo"
Cohesion: 0.16
Nodes (12): Equipo, Liga, date, datetime, rango_utc_dia_partidos(), Límites UTC-naive para un día calendario de America/Guayaquil., _crear_schema_si_falta(), Aísla la suite de la base de PRODUCCIÓN. El `.env` de desarrollo apunta a la… (+4 more)

### Community 49 - "mis_predicciones_screen.dart"
Cohesion: 0.08
Nodes (24): ../../domain/usecases/get_predicciones_mias.dart, PrediccionesDePartido, actual, _cargando, _cargar, createState, _error, _filtro (+16 more)

### Community 53 - "recomendadas_screen.dart"
Cohesion: 0.06
Nodes (33): ../../domain/usecases/get_recomendadas.dart, _autoRefresh, _cargando, _cargar, color, _CombinadasTab, controller, createState (+25 more)

### Community 56 - "BetML_Pro_Informe_Tecnico_v3.md"
Cohesion: 0.11
Nodes (18): **1. Estado Actual del Proyecto**, **2.1 Fuente 1 — API-Football**, **2.2 Fuente 2 — Sofascore (Playwright)**, **2.3 Mapeo y Cruce de Fuentes**, **2. Pipeline ETL Dual — API-Football + Sofascore**, **3. Feature Engineering — 36 Variables del Modelo**, **4.1 Modelos de Gradient Boosting (XGBoost + LightGBM)**, **4.2 Red Neuronal MLP — Modelo Multiobjetivo** (+10 more)

### Community 57 - "AnalisisRepository"
Cohesion: 0.16
Nodes (12): ../entities/analisis_avanzado.dart, AnalisisRepositoryImpl, AnalisisRepository, GetJugadoresPartido, _repository, GetKellyMercados, _repository, GetKellyPortafolio (+4 more)

### Community 58 - "analizar_captura_screen.dart"
Cohesion: 0.12
Nodes (16): ../../data/datasources/analisis_imagen_remote_ds.dart, _analizar, AnalizarCapturaScreen, _AnalizarCapturaScreenState, build, _bytes, _cargando, createState (+8 more)

### Community 61 - "job_alineaciones.py"
Cohesion: 0.14
Nodes (18): LigaSofascoreTorneo, Ids de torneo de Sofascore aprendidos para una liga nuestra. Una liga nuestra…, filtrar_candidatos(), _parecido(), Encuentra el id de torneo de Sofascore de una liga nuestra cuando…, True si comparten alguna palabra significativa (por raíz, para que 'Friendlies'…, [(torneo_id, nombre)] de TODOS los torneos con partidos ese día. La lista es la…, De la lista del día, los que se parecen por nombre a nuestra liga. Sin… (+10 more)

### Community 64 - "generar_resumen"
Cohesion: 0.31
Nodes (9): generar_resumen(), generar_resumen_h2h(), Por qué el modelo predijo lo que predijo — sin llamar a un LLM en cada request…, generar_resumen es texto puro sobre números ya calculados — sin DB, sin modelo…, test_caso_parejo_no_fuerza_ganador(), test_feature_invertido_menor_gana(), test_h2h_resumen_texto(), test_h2h_sin_historial_devuelve_none() (+1 more)

### Community 71 - "PartidoService"
Cohesion: 0.22
Nodes (9): PartidoService, Session, Lógica de negocio relacionada a partidos. Ensambla los datos de múltiples…, Convierte un objeto Partido en dict con datos relacionados. con_prediccion=True…, con_prediccion era un parámetro muerto (bug real encontrado en sesión:…, test_get_detalle_incluye_nombres_reales_no_ids(), test_get_detalle_partido_inexistente_devuelve_none(), test_get_partidos_hoy_cada_fila_trae_clave_prediccion() (+1 more)

### Community 72 - "analisis_avanzado_model.dart"
Cohesion: 0.13
Nodes (14): ../../domain/entities/analisis_avanzado.dart, fromJson, JugadoresPartidoModel, JugadorMercadoModel, KellyAnalisisModel, KellyMercadoModel, KellyPortafolioModel, MercadoPortafolioModel (+6 more)

### Community 73 - "crear_tablas"
Cohesion: 0.14
Nodes (24): crear_tablas(), main(), anclar_si_corresponde(), buscar_candidatos(), equipos_de_la_liga(), Resolución de equipos/liga por nombre de Sofascore contra la BD propia.…, Una vez confirmado (por cruce con Partido: rival+fecha) cuál candidato era el…, id en NUESTRA BD de una liga por nombre (distinto del id de Sofascore usado… (+16 more)

### Community 74 - "design_system.dart"
Cohesion: 0.06
Nodes (32): action, actions, AppHeader, AppRootBackGuard, _AppRootBackGuardState, AppSecondaryBackGuard, AppStateView, build (+24 more)

### Community 75 - "BetML Pro — handoff operativo (2026-08-14)"
Cohesion: 0.12
Nodes (16): 10. Rediseño UX/UI móvil, 11. Pendientes priorizados, 12. Prompt para retomar, 1. Estado actual, 2. Producción y despliegue, 3. Red de seguridad y pruebas, 4. Autenticación y seguridad, 5. Rendimiento medido (+8 more)

### Community 76 - "parlay.dart"
Cohesion: 0.12
Nodes (15): double?, bankroll, cuota, cuotaCombinada, esValueBet, ev, mercado, parlayId (+7 more)

### Community 77 - "auth_provider.dart"
Cohesion: 0.13
Nodes (14): ../../core/auth_storage.dart, autenticado, _autenticar, _cargando, _cargarSesion, _dataSource, _error, _google (+6 more)

### Community 78 - "widget_test.dart"
Cohesion: 0.11
Nodes (16): dart:io, File, main, selection, main, main, _noop, package:flutter_test/flutter_test.dart (+8 more)

### Community 79 - "api_client.py"
Cohesion: 0.06
Nodes (40): PresupuestoApiFootball, Contador de requests gastadas a API-Football por día — el plan free da 100/día,…, _fecha_hoy(), get_estadisticas_equipo(), get_fixtures_hoy(), get_h2h(), get_standings(), correr_job_odds_en_vivo() (+32 more)

### Community 80 - "partido_remote_ds.dart"
Cohesion: 0.17
Nodes (11): _client, _get, getDetalle, _getList, getPrediccionEnVivo, getPrediccionesHoy, getPrediccionesMias, getRecomendadas (+3 more)

### Community 81 - "fecha_hoy_partidos"
Cohesion: 0.19
Nodes (16): fecha_hoy_partidos(), Día futbolístico actual en Ecuador, independiente del TZ del proceso., correr_job_partidos_en_vivo(), _hay_algo_para_actualizar(), datetime, Refresca marcador/estado de los partidos de HOY mientras se juegan, y cierra…, correr_pipeline(), correr_pipeline_fecha() (+8 more)

### Community 82 - "stats_screen.dart"
Cohesion: 0.12
Nodes (19): ChangeNotifier, ../../core/product_analytics.dart, AppColors, StatsProvider, build, c, color, createState (+11 more)

### Community 83 - "test_sofascore_en_vivo.py"
Cohesion: 0.21
Nodes (14): _estado_desde_evento(), _goles_desde(), _minuto_desde_evento(), Actualiza estado/goles/minuto de los partidos de hoy desde Sofascore. Un…, Goles del TIEMPO REGLAMENTARIO. Ojo con "current": en un partido definido por…, Minuto en curso, derivado de cuándo arrancó el período actual — Sofascore no…, _sincronizar_marcadores(), Traducción de un evento de Sofascore a nuestro modelo — lógica pura, sin DB ni… (+6 more)

### Community 84 - "backtest_walk_forward.py"
Cohesion: 0.16
Nodes (17): evaluar_mlp(), main(), _predecir(), DataFrame, ndarray, Walk-forward bajo demanda para la cabeza 1X2 del MLP., evaluar_walk_forward(), guardar_reporte() (+9 more)

### Community 85 - "odds_api_io.py"
Cohesion: 0.26
Nodes (12): _decimal(), _linea(), parsear_bookmakers(), Cuotas desde odds-api.io. Cobertura enorme (~4600 partidos no jugados en una…, 0.5 -> '0_5', -1.25 -> 'm1_25' (mismo formato que el resto)., A las claves odds_* de kelly.py, respetando el orden de CASAS., Parser de odds-api.io — datos calcados de la respuesta real para Tobol Kostanay…, test_betano_manda_sobre_bet365_en_el_mismo_mercado() (+4 more)

### Community 86 - "PrediccionService"
Cohesion: 0.24
Nodes (8): estimar_fraccion_restante(), Fracción del partido que falta jugar (0-1), para escalar el xG pre-partido en…, PrediccionService, Partido, Recalcula 1X2 y mercados de gol EN VIVO dado el marcador y minuto actuales — no…, Este servicio orquesta el flujo completo de las predicciones, Genera lista de mercados recomendados según las probabilidades del modelo. Solo…, persistir=True guarda la predicción para tracking de MLOps (ver…

### Community 95 - "auth_client.dart"
Cohesion: 0.17
Nodes (11): ../auth_storage.dart, ../constants.dart, dart:typed_data, AuthClient, _enviarCopia, _inner, _refreshEnCurso, _renovar (+3 more)

### Community 96 - "division_temporal"
Cohesion: 0.23
Nodes (15): brier_confianza_elegida(), division_temporal(), DataFrame, Evaluación de modelos respetando el orden real de los partidos., Reserva el bloque cronológico reciente sin partir un mismo día., Genera ventanas expansivas; cada validación ocurre después del train., Brier binario de la clase elegida: confianza vs acertó/falló., ventanas_walk_forward() (+7 more)

### Community 97 - "analisis_imagen.dart"
Cohesion: 0.14
Nodes (13): aviso, avisos, cuotaDisponible, edge, mercado, nombreLegible, partidoId, probabilidad (+5 more)

### Community 98 - "predicciones_recomendadas"
Cohesion: 0.38
Nodes (6): predicciones_recomendadas(), Escanea TODOS los partidos de HOY con predicción + cuotas guardadas y arma tres…, correr_job_guardar_recomendadas(), Guarda las apuestas recomendadas del día para que se cierren solas contra el…, Solo mira las del SISTEMA (usuario_id NULL). Si mirara todas, que un usuario…, _ya_guardada()

### Community 99 - "modelos.py"
Cohesion: 0.19
Nodes (19): apuesta_combinada(), GuardarMercadosRequest, ParlayRequest, BaseModel, Apuesta combinada (parlay/acumulada) — varias selecciones de partidos DISTINTOS…, SeleccionParlay, Base, Parlay (+11 more)

### Community 100 - "ejecutar"
Cohesion: 0.24
Nodes (9): ejecutar(), main(), Publica un APK versionado de BetML sin borrar versiones anteriores.…, archivos_a_subir(), main(), mkdir_p(), Sube BetML Pro al servidor y reconstruye los contenedores. Mismo patrón que el…, Crea los directorios que falten, pero SOLO por debajo de REMOTO. Recorrer desde… (+1 more)

### Community 101 - "_Handler"
Cohesion: 0.40
Nodes (3): _Handler, main(), Túnel SSH a la base de producción, para desarrollar en local contra los datos…

### Community 102 - "timedelta"
Cohesion: 0.32
Nodes (12): _necesita_actualizacion(), Lógica pura (sin DB) — separada para poder testearla sin que partidos reales de…, _partido(), datetime, La guardia de job_partidos_en_vivo decide si vale la pena gastar un request de…, Bug real del 13/08/2026: ese día quedó con CERO partidos en la base y la app…, test_dia_sin_partidos_dispara_actualizacion(), test_partido_en_vivo_dispara_actualizacion() (+4 more)

### Community 103 - "test_calibracion_produccion.py"
Cohesion: 0.13
Nodes (22): ajustar_desde_predicciones(), calcular_factor(), cargar(), corregir(), familia_de(), El sistema aprende de sus propios errores, por tipo de mercado. La idea, en…, Calcula un factor de corrección por familia de mercado. Mira TODAS las…, Aplica lo aprendido. Sin datos de esa familia devuelve la probabilidad tal cual… (+14 more)

### Community 104 - "migrar_bd.py"
Cohesion: 0.50
Nodes (3): _db_url_local(), dump_local(), Copia la base local al Postgres de producción (una sola vez, para arrancar con…

### Community 105 - "test_guardador_no_regresa.py"
Cohesion: 0.21
Nodes (12): db(), _fixture(), _limpiar(), Dos fuentes escriben sobre la misma fila de Partido (API-Football en…, Payload de API-Football con lo mínimo que lee guardar_partido., test_no_borra_el_marcador_cuando_la_otra_fuente_no_lo_tiene(), test_si_actualiza_cuando_la_fuente_trae_datos_de_verdad(), dos_partidos_ft() (+4 more)

### Community 106 - "job_odds_sofascore.py"
Cohesion: 0.20
Nodes (15): _a_decimal(), correr_job_odds_sofascore(), _linea_a_clave(), parsear_mercados(), _partidos_a_cotizar(), Cuotas desde Sofascore — reemplazo gratis de job_odds.py. Motivo: el plan free…, 1/5" -> 1.20, "19/4" -> 5.75, "9/1" -> 10.0, 2.5' -> '2_5', '-1.5' -> 'm1_5' (mismo formato que montecarlo.py y job_odds.py,… (+7 more)

### Community 107 - "resolver_mercado.py"
Cohesion: 0.31
Nodes (8): Partido, Resuelve si una selección de cualquier mercado ganó o perdió, dado el resultado…, True si la selección ganó, False si perdió, None si no se puede resolver…, resolver_mercado(), _resultado_1x2(), _stats(), test_aplana_mercado_jugador_con_clave_estable(), test_resuelve_mercado_jugador_con_stat_real()

### Community 108 - "prediccion_service.py"
Cohesion: 0.20
Nodes (13): _correr_montecarlo_partido(), Corre Monte Carlo para un partido con datos anteriores al inicio. El xG del…, encoger(), estimar_xg_prepartido(), medias_globales(), Medias globales de córners/tarjetas y encogimiento hacia ellas. Por qué existe:…, Promedios por partido y por localía. Se calculan una vez por proceso — son de…, Mezcla el promedio del equipo con la media global. Sin muestra devuelve la… (+5 more)

### Community 109 - "analizar_mercados_kelly"
Cohesion: 0.17
Nodes (13): factor_confianza(), Cuánto confiar en la calibración de esta clase en este rango de probabilidad,…, analizar_mercados_kelly(), construir_lista_mercados(), _expandir_over_under(), De un dict {'over_2_5':0.55,'under_2_5':0.45,...} arma tuplas (nombre_mercado,…, Analiza todos los mercados de un partido y calcula el stake óptimo para cada…, (nombre, prob, odds_key, clase_calibracion|None) de todos los mercados… (+5 more)

### Community 110 - "analisis_imagen_model.dart"
Cohesion: 0.29
Nodes (6): ../../domain/entities/analisis_imagen.dart, AnalisisImagenResultadoModel, fromJson, SeleccionImagenModel, AnalisisImagenResultado, SeleccionImagen

### Community 112 - "prediction_coupon_provider.dart"
Cohesion: 0.10
Nodes (19): ProductAnalytics, track, clear, count, CouponSelection, forMatch, input, isEmpty (+11 more)

### Community 113 - "recomendadas_model.dart"
Cohesion: 0.13
Nodes (14): ../../domain/entities/recomendadas.dart, ApuestaIndividualModel, CombinadaMismoPartidoModel, fromJson, MercadoCombinadaModel, ParlaySugeridoModel, PataParlayModel, RecomendadasModel (+6 more)

### Community 114 - "clay.dart"
Cohesion: 0.13
Nodes (14): EdgeInsets, build, child, ClayButton, ClayContainer, icon, label, loading (+6 more)

### Community 115 - "String?"
Cohesion: 0.21
Nodes (11): ../../data/datasources/auth_remote_ds.dart, AuthProvider, build, _cargando, createState, _email, initState, PerfilScreen (+3 more)

### Community 116 - "Odds"
Cohesion: 0.23
Nodes (12): Odds, Cuotas reales de casas de apuestas — API-Football /odds (gratis por fixture_id,…, probabilidades_mercado_1x2(), Session, Lectura de cuotas guardadas por job_odds.py — mejor cuota disponible por…, Probabilidades implícitas sin margen cuando existen las tres cuotas. Es una…, partidos_sin_cuotas(), Partidos por jugarse que todavía no tienen NINGUNA cuota. (+4 more)

### Community 117 - "auth_storage.dart"
Cohesion: 0.18
Nodes (10): AuthStorage, borrarTokens, _claveAccess, _claveRefresh, guardarTokens, leerRefresh, leerToken, _storage (+2 more)

### Community 118 - "auth_remote_ds.dart"
Cohesion: 0.18
Nodes (10): access, AuthRemoteDataSource, AuthTokens, _client, google, login, me, _postTokens (+2 more)

### Community 119 - "partido_service.py"
Cohesion: 0.53
Nodes (6): CacheJson, guardar_cache(), obtener_cache(), Session, test_cache_expirado_se_elimina(), test_cache_json_compartido_guarda_y_recupera()

### Community 120 - "parser.py"
Cohesion: 0.28
Nodes (8): _build_stats_dict(), _extraer_valor(), _limpiar_valor(), parsear_stats_partido(), Construye dos diccionarios planos de stats: uno para local (home) y uno para…, Limpia y convierte cualquier valor de Sofascore a float. Maneja: None, "54%",…, Extrae un valor numérico de las estadísticas. Maneja formatos especiales: "54%"…, Convierte las estadísticas de Sofascore en un objeto EstadisticaSofascore con…

### Community 121 - "auditar_rendimiento_prod.py"
Cohesion: 0.42
Nodes (8): _agrupar(), _comando(), _consultar(), _familia(), main(), Auditoría read-only de recomendaciones cerradas en producción., _resumen(), _wilson()

### Community 122 - "fusionar_equipos.py"
Cohesion: 0.39
Nodes (7): correr_fusion(), encontrar_duplicados(), fusionar(), _normalizar(), _partidos_de(), Fusiona filas duplicadas del mismo equipo. Un club terminaba cargado dos veces…, [(sobreviviente, [a_fusionar...])] por nombre normalizado.

### Community 123 - "analisis_repo_impl.dart"
Cohesion: 0.29
Nodes (6): ../../core/http/auth_client.dart, ../datasources/analisis_remote_ds.dart, ../../domain/repositories/analisis_repository.dart, AnalisisRemoteDataSource, create, _dataSource

### Community 124 - "correr_job_alineaciones"
Cohesion: 0.33
Nodes (6): _fuente_sofascore(), correr_job_alineaciones(), _partidos_elegibles(), Partidos dentro de la ventana, sin importar si ya tienen sofascore_id — eso se…, job_alineaciones(), Cada 15 min — trae la alineación confirmada de Sofascore para partidos que…

### Community 125 - "descargar_dataset_prod.py"
Cohesion: 0.50
Nodes (4): descargar(), _ejecutar(), Path, Descarga en solo lectura el dataset cacheado del scheduler de producción.

### Community 126 - "Q: Why does _post connect test_auth.py to auth_remote_ds.dart and predicciones.py?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Why does _post connect test_auth.py to auth_remote_ds.dart and predicciones.py?, Source Nodes

## Knowledge Gaps
- **613 isolated node(s):** `Config`, `XCTest`, `AuthStorage`, `_claveAccess`, `_claveRefresh` (+608 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Partido` connect `Partido` to `PartidoRepository`, `ensemble.py`, `calibracion.py`, `PrediccionRepository`, `lstm.py`, `test_parser_imagen.py`, `construir_features_partido`, `job_reentrenar_modelos.py`, `job_sofascore_en_vivo.py`, `database.py`, `test_alineaciones.py`, `orquestador.py`, `Equipo`, `job_alineaciones.py`, `PartidoService`, `crear_tablas`, `api_client.py`, `fecha_hoy_partidos`, `PrediccionService`, `modelos.py`, `test_guardador_no_regresa.py`, `job_odds_sofascore.py`, `resolver_mercado.py`, `prediccion_service.py`, `Odds`, `fusionar_equipos.py`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Why does `Prediccion` connect `modelos.py` to `PrediccionRepository`, `predicciones_recomendadas`, `ensemble.py`, `test_calibracion_produccion.py`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Why does `Failure` connect `failures.dart` to `analisis_avanzado_screen.dart`, `recomendadas_screen.dart`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `Partido` (e.g. with `Base` and `CodificadorTemporal`) actually correct?**
  _`Partido` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `PartidoRepository` (e.g. with `GuardarMercadosRequest` and `ParlayRequest`) actually correct?**
  _`PartidoRepository` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `PrediccionRepository` (e.g. with `GuardarMercadosRequest` and `ParlayRequest`) actually correct?**
  _`PrediccionRepository` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `PrediccionService` (e.g. with `GuardarMercadosRequest` and `ParlayRequest`) actually correct?**
  _`PrediccionService` has 8 INFERRED edges - model-reasoned connections that need verification._