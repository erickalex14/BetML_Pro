# Graph Report - BetML_Pro  (2026-08-13)

## Corpus Check
- 187 files · ~281,909 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1760 nodes · 3209 edges · 112 communities (104 shown, 8 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 71 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8656e642`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- tests/test_kelly.py
- test_auth.py
- api_client.py
- PartidoRepository
- PartidoRepository
- scheduler.py
- job_reentrenar_modelos.py
- dataset.py
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
- StatelessWidget
- get
- constants.dart
- simular_partido
- detalle_screen.dart
- partidos_provider.dart
- simular_jugadores_partido
- database.py
- stats_provider.dart
- test_alineaciones.py
- orquestador.py
- manifest.json
- partido_model.dart
- analisis_avanzado_screen.dart
- analisis_avanzado.dart
- the_odds_api.py
- failures.dart
- recomendadas.dart
- main.dart
- parlay_screen.dart
- auth_remote_ds.dart
- stats_screen.dart
- package:flutter/material.dart
- FlutterActivity
- modelos.py
- mis_predicciones_screen.dart
- recomendadas_screen.dart
- BetML_Pro_Informe_Tecnico_v3.md
- ../../core/errors/failures.dart
- analizar_captura_screen.dart
- job_alineaciones.py
- generar_resumen
- Partido
- Prediccion
- PartidoService
- analisis_avanzado_model.dart
- analisis_imagen.dart
- clay.dart
- BetML Pro — Estado al 2026-08-13
- parlay.dart
- auth_provider.dart
- _necesita_actualizacion
- job_odds_en_vivo.py
- partido_remote_ds.dart
- job_partidos_en_vivo.py
- analisis_remote_ds.dart
- test_sofascore_en_vivo.py
- partido_repo_impl.dart
- analisis_imagen_model.dart
- ../../domain/entities/parlay.dart
- frontend
- LaunchImage.imageset/README.md
- bool?
- DateTime?
- prediccion_service.py
- ModeloService
- test_odds_en_vivo.py
- job_guardar_recomendadas.py
- encoger
- deploy_betml.py
- _Handler
- odds_api_io.py
- test_calibracion_produccion.py
- migrar_bd.py
- ensemble.py
- parsear_mercados
- .predecir
- String?
- correr_job_odds
- GNNEquipoJugador

## God Nodes (most connected - your core abstractions)
1. `Partido` - 45 edges
2. `PartidoRepository` - 36 edges
3. `PrediccionRepository` - 35 edges
4. `get()` - 31 edges
5. `SofascoreCliente` - 30 edges
6. `crear_tablas()` - 29 edges
7. `PrediccionService` - 29 edges
8. `simular_partido()` - 26 edges
9. `Equipo` - 21 edges
10. `predecir_ensemble()` - 21 edges

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

## Communities (112 total, 8 thin omitted)

### Community 0 - "tests/test_kelly.py"
Cohesion: 0.09
Nodes (35): factor_confianza(), Cuánto confiar en la calibración de esta clase en este rango de probabilidad,…, analizar_mercados_kelly(), calcular_kelly(), construir_lista_mercados(), _expandir_over_under(), kelly_portfolio(), probabilidad_ruina() (+27 more)

### Community 1 - "test_auth.py"
Cohesion: 0.14
Nodes (31): health(), root(), startup(), login(), LoginRequest, me(), BaseModel, Session (+23 more)

### Community 2 - "api_client.py"
Cohesion: 0.14
Nodes (19): PresupuestoApiFootball, Contador de requests gastadas a API-Football por día — el plan free da 100/día,…, _fecha_hoy(), get_estadisticas_equipo(), get_fixtures_hoy(), get_h2h(), get_standings(), _hoy_utc() (+11 more)

### Community 3 - "PartidoRepository"
Cohesion: 0.23
Nodes (3): PartidoRepository, Partido, Session

### Community 4 - "PartidoRepository"
Cohesion: 0.11
Nodes (19): ../entities/partido.dart, ../entities/prediccion.dart, ../entities/recomendadas.dart, PartidoRepositoryImpl, PartidoRepository, GetDetallePartido, _repository, GetPartidosHoy (+11 more)

### Community 5 - "scheduler.py"
Cohesion: 0.14
Nodes (21): correr_job_estadisticas(), correr_orquestador_odds(), iniciar_scheduler(), job_alineaciones(), job_cerrar_predicciones(), job_estadisticas(), job_fixtures_manana(), job_odds_cascada() (+13 more)

### Community 6 - "job_reentrenar_modelos.py"
Cohesion: 0.14
Nodes (20): construir_grafo(), Construcción del grafo equipo-jugador para la GNN. Dos tipos de nodo (equipo,…, Devuelve (grafo, id_a_indice_equipo, id_a_indice_jugador). fecha_corte=None usa…, entrenar_modelo(), guardar_modelo(), DataFrame, entrenar_gnn(), guardar_gnn() (+12 more)

### Community 7 - "dataset.py"
Cohesion: 0.17
Nodes (17): generar_dataset(), DataFrame, ajustar_calibracion(), calibrar_probabilidades(), cargar_calibracion(), guardar_calibracion(), ndarray, Path (+9 more)

### Community 8 - "PrediccionRepository"
Cohesion: 0.05
Nodes (56): GuardarMercadosRequest, ParlayRequest, BaseModel, SeleccionParlay, Session, Métricas de rendimiento del modelo — MLOps tracking. Incluye…, stats_modelo(), Parlay (+48 more)

### Community 9 - "lstm.py"
Cohesion: 0.13
Nodes (12): CodificadorTemporal, _DatasetSecuencias, _pad_izquierda(), predecir_lstm(), DataFrame, Dataset, ndarray, Red LSTM — captura la dimensión temporal que XGBoost y el MLP no ven.… (+4 more)

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
Cohesion: 0.14
Nodes (30): analizar_captura(), apuesta_combinada(), _correr_montecarlo_partido(), guardar_mercados(), kelly_partido(), kelly_portafolio_partido(), montecarlo_partido(), prediccion_en_vivo() (+22 more)

### Community 16 - "calculador.py"
Cohesion: 0.24
Nodes (14): calcular_forma(), calcular_h2h(), calcular_rating_jugadores(), calcular_stats_sofascore(), calcular_win_rate(), construir_features_partido(), obtener_secuencia_equipo(), Partido (+6 more)

### Community 17 - "mlp.py"
Cohesion: 0.17
Nodes (12): cargar_mlp(), _DatasetMultiObjetivo, entrenar_mlp(), guardar_mlp(), _perdida_batch(), DataFrame, Dataset, Path (+4 more)

### Community 18 - "job_sofascore_en_vivo.py"
Cohesion: 0.09
Nodes (33): EstadisticaSofascore, Stats avanzadas del partido desde Sofascore. xG, presiones, duelos, pases…, main(), anclar_si_corresponde(), Una vez confirmado (por cruce con Partido: rival+fecha) cuál candidato era el…, guardar_jugadores(), guardar_stats_sofascore(), Session (+25 more)

### Community 19 - "theme.dart"
Cohesion: 0.05
Nodes (42): AppColors get, BuildContext, Color bg, bg2,, Color brick,, Color ledger,, Color line,, Color pitch,, Color shadowDark, (+34 more)

### Community 20 - "StatelessWidget"
Cohesion: 0.06
Nodes (38): dart:async, double width,, _EquipoSeccion, _JugadoresTab, _JugadorRow, _MensajeError, _MercadoKellyRow, _MercadosPorCategoria (+30 more)

### Community 21 - "get"
Cohesion: 0.23
Nodes (12): detalle_partido(), partidos_hoy(), partidos_liga(), prediccion_partido(), Session, mercados_jugadores(), prediccion_ensemble(), predicciones_mias() (+4 more)

### Community 22 - "constants.dart"
Cohesion: 0.08
Nodes (25): analizarCaptura, ApiConstants, AppConstants, appName, appVersion, authLogin, authMe, authRegistro (+17 more)

### Community 23 - "simular_partido"
Cohesion: 0.13
Nodes (25): cargar_rho(), _grid_marcadores(), _handicap_asiatico(), ndarray, Simula un partido N veces muestreando de la distribución conjunta Poisson…, Hándicap asiático derivado de la diferencia de goles ya simulada (no consume…, Reparte los goles YA simulados del partido completo entre 1T/2T — cada gol,…, Mercado over/under genérico vía Poisson independiente (corners, tarjetas) — sin… (+17 more)

### Community 24 - "detalle_screen.dart"
Cohesion: 0.07
Nodes (29): ../../domain/usecases/get_detalle_partido.dart, ../../domain/usecases/get_prediccion_en_vivo.dart, _autoRefresh, build, _cargando, _cargar, child, createState (+21 more)

### Community 25 - "partidos_provider.dart"
Cohesion: 0.14
Nodes (13): ../../domain/usecases/get_partidos_hoy.dart, _cargando, cargarPartidosHoy, _error, _fecha, _getPartidosHoy, _ligaFiltro, ligasDisponibles (+5 more)

### Community 26 - "simular_jugadores_partido"
Cohesion: 0.29
Nodes (9): calcular_forma_jugador(), obtener_titulares_probables(), Session, Jugadores titulares en al menos min_apariciones (40% default) de los últimos…, Promedio de stats del jugador en sus últimos n partidos disputados antes de…, Simulación Monte Carlo de mercados individuales de jugador — tiros, tiros al…, Simula mercados individuales para el XI de ambos equipos. Usa la alineación…, simular_jugador() (+1 more)

### Community 27 - "database.py"
Cohesion: 0.13
Nodes (18): crear_tablas(), correr_job_historico(), buscar_candidatos(), equipos_de_la_liga(), Resolución de equipos/liga por nombre de Sofascore contra la BD propia.…, id en NUESTRA BD de una liga por nombre (distinto del id de Sofascore usado…, Query base de equipos, acotada a los que ya jugaron en esta liga (evita que la…, Devuelve [(Equipo, score), ...]. score=None si vino de un sofascore_id ya… (+10 more)

### Community 28 - "stats_provider.dart"
Cohesion: 0.17
Nodes (11): bool get, ../../data/repositories/partido_repo_impl.dart, ../../domain/usecases/get_stats_modelo.dart, StatsModeloModel, StatsModelo, _cargando, cargar, _error (+3 more)

### Community 29 - "test_alineaciones.py"
Cohesion: 0.20
Nodes (15): EstadisticaJugador, obtener_lineup_confirmada(), Features a nivel jugador — para los mercados individuales (tiros, tiros al…, XI real confirmado por Sofascore para ESTE partido (job_alineaciones.py lo trae…, _equipo_temporal(), _limpiar(), _partido_temporal(), Bug real encontrado en sesión: Endrick (ya no juega en Lyon) seguía apareciendo… (+7 more)

### Community 30 - "orquestador.py"
Cohesion: 0.15
Nodes (14): Odds, Cuotas reales de casas de apuestas — API-Football /odds (gratis por fixture_id,…, Lectura de cuotas guardadas por job_odds.py — mejor cuota disponible por…, _buscar_evento(), Cruza por nombres + fecha, con la misma similitud que el anclaje de Sofascore…, traer_cuotas(), _fuente_odds_api_io(), _fuente_sofascore() (+6 more)

### Community 31 - "manifest.json"
Cohesion: 0.18
Nodes (10): background_color, description, display, icons, name, orientation, prefer_related_applications, short_name (+2 more)

### Community 32 - "partido_model.dart"
Cohesion: 0.15
Nodes (12): ../../domain/entities/partido.dart, FactorModel, fromJson, MercadoModel, PartidoModel, PrediccionEnVivoModel, PrediccionGuardadaModel, PrediccionModel (+4 more)

### Community 33 - "analisis_avanzado_screen.dart"
Cohesion: 0.04
Nodes (57): ../../data/repositories/analisis_repo_impl.dart, ../../domain/usecases/get_jugadores_partido.dart, ../../domain/usecases/get_kelly_mercados.dart, ../../domain/usecases/get_kelly_portafolio.dart, ../../domain/usecases/guardar_mercados.dart, _abrirDetalle, _abrirDetalleJugador, AnalisisAvanzadoScreen (+49 more)

### Community 34 - "analisis_avanzado.dart"
Cohesion: 0.04
Nodes (48): asistenciasOverUnder, asistenciasPromedio, atajadasOverUnder, atajadasPromedio, clave, cuota, cuotaJusta, edge (+40 more)

### Community 35 - "the_odds_api.py"
Cohesion: 0.22
Nodes (14): _buscar_partido(), _decimal(), _parsear_evento(), Cuotas desde The Odds API (https://the-odds-api.com). Rinde mucho por llamada:…, Cruza por nombres de equipo + fecha cercana., Pide una vez por liga presente entre los partidos sin cuotas., Del JSON de un evento a las claves odds_* que usa kelly.py. Se queda con la…, _similitud() (+6 more)

### Community 36 - "failures.dart"
Cohesion: 0.39
Nodes (7): Failure, mensaje, NetworkFailure, NotFoundFailure, ParseFailure, ServerFailure, statusCode

### Community 37 - "recomendadas.dart"
Cohesion: 0.05
Nodes (45): ../../domain/entities/recomendadas.dart, ApuestaIndividualModel, CombinadaMismoPartidoModel, fromJson, MercadoCombinadaModel, ParlaySugeridoModel, PataParlayModel, RecomendadasModel (+37 more)

### Community 38 - "main.dart"
Cohesion: 0.08
Nodes (23): core/router.dart, buildRouter, _auth, BetMLApp, _BetMLAppState, build, createState, main (+15 more)

### Community 39 - "parlay_screen.dart"
Cohesion: 0.08
Nodes (28): ../../data/datasources/parlay_remote_ds.dart, PartidosProvider, build, initState, build, _calculando, _calcular, createState (+20 more)

### Community 40 - "auth_remote_ds.dart"
Cohesion: 0.10
Nodes (22): ../auth_storage.dart, Client, ../../core/constants.dart, dart:convert, AuthClient, _inner, send, AnalisisImagenRemoteDataSource (+14 more)

### Community 41 - "stats_screen.dart"
Cohesion: 0.06
Nodes (39): ChangeNotifier, Color, ../../data/datasources/auth_remote_ds.dart, AppColors, AuthProvider, StatsProvider, build, _campo (+31 more)

### Community 42 - "package:flutter/material.dart"
Cohesion: 0.09
Nodes (21): clay.dart, ../../core/theme.dart, dart:math, AppBottomNav, AppTab, build, current, _item (+13 more)

### Community 44 - "modelos.py"
Cohesion: 0.10
Nodes (28): Base, Equipo, EstadisticaPartido, Liga, Partido, guardar_partido(), Session, Crea el equipo si no existe. Si ya existe pero le falta el logo (723 equipos ya… (+20 more)

### Community 49 - "mis_predicciones_screen.dart"
Cohesion: 0.09
Nodes (23): ../../domain/usecases/get_predicciones_mias.dart, PrediccionesDePartido, actual, build, _cargando, _cargar, createState, _error (+15 more)

### Community 53 - "recomendadas_screen.dart"
Cohesion: 0.08
Nodes (26): ../../domain/usecases/get_recomendadas.dart, build, _cargando, _cargar, color, _CombinadasTab, createState, _dato (+18 more)

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
Cohesion: 0.09
Nodes (34): LigaSofascoreTorneo, Ids de torneo de Sofascore aprendidos para una liga nuestra. Una liga nuestra…, ahora_partidos(), datetime, Ahora" en la misma referencia que Partido.fecha, para poder compararlos.…, filtrar_candidatos(), _parecido(), Encuentra el id de torneo de Sofascore de una liga nuestra cuando… (+26 more)

### Community 64 - "generar_resumen"
Cohesion: 0.31
Nodes (9): generar_resumen(), generar_resumen_h2h(), Por qué el modelo predijo lo que predijo — sin llamar a un LLM en cada request…, generar_resumen es texto puro sobre números ya calculados — sin DB, sin modelo…, test_caso_parejo_no_fuerza_ganador(), test_feature_invertido_menor_gana(), test_h2h_resumen_texto(), test_h2h_sin_historial_devuelve_none() (+1 more)

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

### Community 75 - "BetML Pro — Estado al 2026-08-13"
Cohesion: 0.20
Nodes (9): 1. PRODUCCIÓN — ya andando, 2. Trampas de deploy — ya costaron tiempo, no repetirlas, 3. Agenda del scheduler, 4. Cómo aprende el modelo (importante, hubo confusión), 5. Bugs de correctitud encontrados (todos con test que los fija), 6. Anclaje de `sofascore_id` — el cuello de botella, 7. Arquitectura, 8. Pendientes (+1 more)

### Community 76 - "parlay.dart"
Cohesion: 0.14
Nodes (13): bankroll, cuotaCombinada, esValueBet, ev, mercado, parlayId, ParlaySeleccionInput, partidoId (+5 more)

### Community 77 - "auth_provider.dart"
Cohesion: 0.15
Nodes (12): ../../core/auth_storage.dart, autenticado, _autenticar, _cargando, _cargarSesion, _dataSource, _error, login (+4 more)

### Community 78 - "_necesita_actualizacion"
Cohesion: 0.32
Nodes (11): _necesita_actualizacion(), Lógica pura (sin DB) — separada para poder testearla sin que partidos reales de…, _partido(), datetime, La guardia de job_partidos_en_vivo decide si vale la pena gastar un request de…, Bug real del 13/08/2026: ese día quedó con CERO partidos en la base y la app…, test_dia_sin_partidos_dispara_actualizacion(), test_partido_en_vivo_dispara_actualizacion() (+3 more)

### Community 79 - "job_odds_en_vivo.py"
Cohesion: 0.19
Nodes (12): correr_job_odds_en_vivo(), _hay_partidos_en_vivo(), Job de cuotas EN VIVO — GET /odds/live (gratis en el plan actual, verificado en…, _linea_a_clave(), _parsear_btts(), _parsear_handicap(), _parsear_match_winner(), _parsear_over_under() (+4 more)

### Community 80 - "partido_remote_ds.dart"
Cohesion: 0.17
Nodes (11): _client, _get, getDetalle, _getList, getPrediccionEnVivo, getPrediccionesHoy, getPrediccionesMias, getRecomendadas (+3 more)

### Community 81 - "job_partidos_en_vivo.py"
Cohesion: 0.19
Nodes (13): correr_job_partidos_en_vivo(), _hay_algo_para_actualizar(), datetime, Refresca marcador/estado de los partidos de HOY mientras se juegan, y cierra…, correr_pipeline(), correr_pipeline_fecha(), poblar_ligas(), Igual que correr_pipeline() pero para una fecha específica. Se usa para pre-… (+5 more)

### Community 82 - "analisis_remote_ds.dart"
Cohesion: 0.25
Nodes (7): _client, _get, getJugadores, getKelly, getKellyPortafolio, guardarMercados, ../models/analisis_avanzado_model.dart

### Community 83 - "test_sofascore_en_vivo.py"
Cohesion: 0.23
Nodes (12): _estado_desde_evento(), _goles_desde(), _minuto_desde_evento(), Goles del TIEMPO REGLAMENTARIO. Ojo con "current": en un partido definido por…, Minuto en curso, derivado de cuándo arrancó el período actual — Sofascore no…, Traducción de un evento de Sofascore a nuestro modelo — lógica pura, sin DB ni…, test_estado_en_juego_sin_descripcion_no_inventa_periodo(), test_estado_en_juego_usa_la_descripcion_del_periodo() (+4 more)

### Community 84 - "partido_repo_impl.dart"
Cohesion: 0.14
Nodes (12): ../../core/http/auth_client.dart, ../datasources/analisis_remote_ds.dart, ../datasources/partido_remote_ds.dart, ../../domain/entities/prediccion.dart, ../../domain/repositories/analisis_repository.dart, ../../domain/repositories/partido_repository.dart, AnalisisRemoteDataSource, PartidoRemoteDataSource (+4 more)

### Community 85 - "analisis_imagen_model.dart"
Cohesion: 0.29
Nodes (6): ../../domain/entities/analisis_imagen.dart, AnalisisImagenResultadoModel, fromJson, SeleccionImagenModel, AnalisisImagenResultado, SeleccionImagen

### Community 86 - "../../domain/entities/parlay.dart"
Cohesion: 0.40
Nodes (4): ../../domain/entities/parlay.dart, fromJson, ParlayResultadoModel, ParlayResultado

### Community 95 - "prediccion_service.py"
Cohesion: 0.33
Nodes (6): Config, get_settings(), Settings, get_modelo_service(), Session, BaseSettings

### Community 96 - "ModeloService"
Cohesion: 0.27
Nodes (4): ModeloService, DataFrame, ndarray, Gestiona el ciclo de vida del modelo ML

### Community 97 - "test_odds_en_vivo.py"
Cohesion: 0.31
Nodes (6): _parsear_over_under_vivo(), _sin_suspender(), Parsers puros del feed /odds/live — sin DB, sin red. Cubre: filtro de mercados…, test_over_under_vivo_arma_clave_desde_handicap(), test_over_under_vivo_descarta_suspendidos(), test_sin_suspender_filtra_y_devuelve_value_odd()

### Community 98 - "job_guardar_recomendadas.py"
Cohesion: 0.33
Nodes (6): correr_job_guardar_recomendadas(), Guarda las apuestas recomendadas del día para que se cierren solas contra el…, Solo mira las del SISTEMA (usuario_id NULL). Si mirara todas, que un usuario…, _ya_guardada(), job_guardar_recomendadas(), 01:45 — deja registradas las recomendadas del día para que se cierren solas…

### Community 99 - "encoger"
Cohesion: 0.33
Nodes (5): encoger(), medias_globales(), Medias globales de córners/tarjetas y encogimiento hacia ellas. Por qué existe:…, Promedios por partido y por localía. Se calculan una vez por proceso — son de…, Mezcla el promedio del equipo con la media global. Sin muestra devuelve la…

### Community 100 - "deploy_betml.py"
Cohesion: 0.47
Nodes (5): archivos_a_subir(), main(), mkdir_p(), Sube BetML Pro al servidor y reconstruye los contenedores. Mismo patrón que el…, Crea los directorios que falten, pero SOLO por debajo de REMOTO. Recorrer desde…

### Community 101 - "_Handler"
Cohesion: 0.40
Nodes (3): _Handler, main(), Túnel SSH a la base de producción, para desarrollar en local contra los datos…

### Community 102 - "odds_api_io.py"
Cohesion: 0.26
Nodes (12): _decimal(), _linea(), parsear_bookmakers(), Cuotas desde odds-api.io. Cobertura enorme (~4600 partidos no jugados en una…, 0.5 -> '0_5', -1.25 -> 'm1_25' (mismo formato que el resto)., A las claves odds_* de kelly.py, respetando el orden de CASAS., Parser de odds-api.io — datos calcados de la respuesta real para Tobol Kostanay…, test_betano_manda_sobre_bet365_en_el_mismo_mercado() (+4 more)

### Community 103 - "test_calibracion_produccion.py"
Cohesion: 0.14
Nodes (21): ajustar_desde_predicciones(), calcular_factor(), corregir(), familia_de(), El sistema aprende de sus propios errores, por tipo de mercado. La idea, en…, Calcula un factor de corrección por familia de mercado. Mira TODAS las…, Aplica lo aprendido. Sin datos de esa familia devuelve la probabilidad tal cual…, Agrupa las claves de mercado en familias que comparten mecánica. Mismo… (+13 more)

### Community 104 - "migrar_bd.py"
Cohesion: 0.50
Nodes (3): _db_url_local(), dump_local(), Copia la base local al Postgres de producción (una sola vez, para arrancar con…

### Community 105 - "ensemble.py"
Cohesion: 0.22
Nodes (12): predecir_ensemble(), Partido, Ensemble — combina XGBoost, MLP, LSTM y GNN por votación ponderada. El peso de…, persistir=True guarda la predicción para tracking de MLOps (ver…, cargar_metricas_xgboost(), cargar_gnn(), predecir_gnn(), Path (+4 more)

### Community 106 - "parsear_mercados"
Cohesion: 0.23
Nodes (12): _a_decimal(), _linea_a_clave(), parsear_mercados(), 1/5" -> 1.20, "19/4" -> 5.75, "9/1" -> 10.0, 2.5' -> '2_5', '-1.5' -> 'm1_5' (mismo formato que montecarlo.py y job_odds.py,…, De la respuesta de Sofascore a las claves odds_* que usa kelly.py., Parser de cuotas de Sofascore — datos calcados de la respuesta real de…, test_convierte_cuota_fraccionaria_a_decimal() (+4 more)

### Community 107 - ".predecir"
Cohesion: 0.22
Nodes (6): estimar_fraccion_restante(), Fracción del partido que falta jugar (0-1), para escalar el xG pre-partido en…, Partido, Recalcula 1X2 y mercados de gol EN VIVO dado el marcador y minuto actuales — no…, Genera lista de mercados recomendados según las probabilidades del modelo. Solo…, persistir=True guarda la predicción para tracking de MLOps (ver…

### Community 108 - "String?"
Cohesion: 0.25
Nodes (7): build, _fallback, nombre, size, TeamLogo, url, String?

### Community 109 - "correr_job_odds"
Cohesion: 0.33
Nodes (6): correr_job_odds(), _parsear_bookmaker(), {"odds_local": 1.9, ...} de un bookmaker — solo mercados mapeados., _fuente_api_football(), job_odds(), 01:15 — Cuotas reales (hasta 14 bookmakers, gratis vía fixture_id) para los…

## Knowledge Gaps
- **513 isolated node(s):** `Config`, `XCTest`, `AuthStorage`, `_claveToken`, `_storage` (+508 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_post` connect `predicciones.py` to `auth_remote_ds.dart`, `test_auth.py`?**
  _High betweenness centrality (0.424) - this node is a cross-community bridge._
- **Why does `guardar_mercados()` connect `predicciones.py` to `PrediccionRepository`, `test_auth.py`, `PartidoRepository`, `tests/test_kelly.py`?**
  _High betweenness centrality (0.134) - this node is a cross-community bridge._
- **Why does `apuesta_combinada()` connect `predicciones.py` to `PrediccionRepository`, `tests/test_kelly.py`, `PartidoRepository`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `Partido` (e.g. with `Base` and `CodificadorTemporal`) actually correct?**
  _`Partido` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `PartidoRepository` (e.g. with `GuardarMercadosRequest` and `ParlayRequest`) actually correct?**
  _`PartidoRepository` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `PrediccionRepository` (e.g. with `GuardarMercadosRequest` and `ParlayRequest`) actually correct?**
  _`PrediccionRepository` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Config`, `XCTest`, `AuthStorage` to the rest of the system?**
  _513 weakly-connected nodes found - possible documentation gaps or missing edges._