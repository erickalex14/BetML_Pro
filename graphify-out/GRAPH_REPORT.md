# Graph Report - BetML_Pro  (2026-08-13)

## Corpus Check
- 176 files · ~276,705 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1675 nodes · 3001 edges · 105 communities (98 shown, 7 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 64 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a3c2f71c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- simular_partido
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
- StatelessWidget
- get
- constants.dart
- resolver_mercado.py
- detalle_screen.dart
- partidos_provider.dart
- simular_jugadores_partido
- job_crear_fixtures_sofascore.py
- stats_provider.dart
- test_alineaciones.py
- stats_screen.dart
- manifest.json
- partido_model.dart
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
- job_partidos_en_vivo.py
- job_odds_en_vivo.py
- partido_remote_ds.dart
- api_client.py
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
- predicciones_recomendadas
- encoger
- deploy_betml.py
- _Handler
- construir_grafo
- calibracion_produccion.py
- migrar_bd.py

## God Nodes (most connected - your core abstractions)
1. `Partido` - 42 edges
2. `PartidoRepository` - 36 edges
3. `PrediccionRepository` - 32 edges
4. `get()` - 31 edges
5. `PrediccionService` - 29 edges
6. `SofascoreCliente` - 28 edges
7. `crear_tablas()` - 27 edges
8. `simular_partido()` - 26 edges
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

## Communities (105 total, 7 thin omitted)

### Community 0 - "simular_partido"
Cohesion: 0.06
Nodes (58): factor_confianza(), Cuánto confiar en la calibración de esta clase en este rango de probabilidad,…, analizar_mercados_kelly(), calcular_kelly(), _expandir_over_under(), kelly_portfolio(), probabilidad_ruina(), Kelly de portafolio — para cuando se apuesta a VARIOS mercados del MISMO… (+50 more)

### Community 1 - "test_auth.py"
Cohesion: 0.12
Nodes (34): login(), LoginRequest, me(), BaseModel, Session, registro(), RegistroRequest, crear_token() (+26 more)

### Community 2 - "presupuesto.py"
Cohesion: 0.22
Nodes (15): PresupuestoApiFootball, Contador de requests gastadas a API-Football por día — el plan free da 100/día,…, hay_presupuesto(), _hoy_utc(), Contador compartido de requests a API-Football por día — el plan free da…, Suma 1 al contador de hoy (crea la fila si hace falta). Devuelve el total usado…, True si queda al menos `minimo` de presupuesto hoy. Los jobs en vivo (baja…, registrar_uso() (+7 more)

### Community 3 - "PartidoRepository"
Cohesion: 0.16
Nodes (7): prediccion_ensemble(), predicciones_mias(), Predicción combinada — XGBoost + MLP + LSTM, votación ponderada por accuracy de…, Historial de predicciones guardadas (ver POST /{id}/guardar-mercados) — para la…, PartidoRepository, Partido, Session

### Community 4 - "PartidoRepository"
Cohesion: 0.11
Nodes (19): ../entities/partido.dart, ../entities/prediccion.dart, ../entities/recomendadas.dart, PartidoRepositoryImpl, PartidoRepository, GetDetallePartido, _repository, GetPartidosHoy (+11 more)

### Community 5 - "scheduler.py"
Cohesion: 0.12
Nodes (24): correr_job_estadisticas(), iniciar_scheduler(), job_alineaciones(), job_cerrar_predicciones(), job_estadisticas(), job_fixtures_manana(), job_guardar_recomendadas(), job_odds() (+16 more)

### Community 6 - "job_reentrenar_modelos.py"
Cohesion: 0.12
Nodes (23): generar_dataset(), DataFrame, ajustar_desde_predicciones(), Ajusta la curva probabilidad-declarada -> frecuencia-real sobre las…, entrenar_modelo(), guardar_modelo(), DataFrame, cargar_gnn() (+15 more)

### Community 7 - "ensemble.py"
Cohesion: 0.13
Nodes (24): ajustar_calibracion(), calibrar_probabilidades(), cargar_calibracion(), guardar_calibracion(), ndarray, Path, Calibración de probabilidades del modelo — necesaria para que Kelly tenga…, Aplica el calibrador de cada clase y renormaliza a que sume 1. (+16 more)

### Community 8 - "PrediccionRepository"
Cohesion: 0.09
Nodes (27): Parlay, Prediccion, Apuesta combinada guardada — ver /predicciones/combinada. acerto=None mientras…, _peso_modelo(), _cerrar_parlays_pendientes(), _cerrar_predicciones_individuales(), _clave_mercado(), correr_job_cerrar_predicciones() (+19 more)

### Community 9 - "lstm.py"
Cohesion: 0.11
Nodes (16): obtener_secuencia_equipo(), Últimos n partidos del equipo (local o visitante, cualquiera de los dos) antes…, cargar_lstm(), CodificadorTemporal, _DatasetSecuencias, _pad_izquierda(), predecir_lstm(), DataFrame (+8 more)

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
Cohesion: 0.08
Nodes (19): Cliente de Sofascore usando Playwright. Lanza un browser Chromium real para…, Arranca el browser y visita Sofascore para obtener cookies., Cierra el browser limpiamente., Hace una request a la API de Sofascore usando el browser. Navega directamente a…, Trae todos los partidos de fútbol de una fecha., Trae estadísticas completas de un partido., Trae alineaciones y stats de jugadores., Trae partidos históricos (ya jugados) de una liga y temporada — /events/last/,… (+11 more)

### Community 15 - "predicciones.py"
Cohesion: 0.11
Nodes (36): analizar_captura(), apuesta_combinada(), _correr_montecarlo_partido(), guardar_mercados(), GuardarMercadosRequest, kelly_partido(), kelly_portafolio_partido(), montecarlo_partido() (+28 more)

### Community 16 - "calculador.py"
Cohesion: 0.28
Nodes (12): calcular_forma(), calcular_h2h(), calcular_rating_jugadores(), calcular_stats_sofascore(), calcular_win_rate(), construir_features_partido(), Partido, Session (+4 more)

### Community 17 - "mlp.py"
Cohesion: 0.17
Nodes (12): cargar_mlp(), _DatasetMultiObjetivo, entrenar_mlp(), guardar_mlp(), _perdida_batch(), DataFrame, Dataset, Path (+4 more)

### Community 18 - "job_sofascore_en_vivo.py"
Cohesion: 0.10
Nodes (31): EstadisticaSofascore, Stats avanzadas del partido desde Sofascore. xG, presiones, duelos, pases…, main(), anclar_si_corresponde(), Una vez confirmado (por cruce con Partido: rival+fecha) cuál candidato era el…, guardar_jugadores(), guardar_stats_sofascore(), Session (+23 more)

### Community 19 - "theme.dart"
Cohesion: 0.05
Nodes (42): AppColors get, BuildContext, Color bg, bg2,, Color brick,, Color ledger,, Color line,, Color pitch,, Color shadowDark, (+34 more)

### Community 20 - "StatelessWidget"
Cohesion: 0.06
Nodes (39): dart:async, double width,, _EquipoSeccion, _JugadoresTab, _JugadorRow, _MensajeError, _MercadoKellyRow, _MercadosPorCategoria (+31 more)

### Community 21 - "get"
Cohesion: 0.19
Nodes (14): health(), root(), detalle_partido(), partidos_hoy(), partidos_liga(), prediccion_partido(), Session, mercados_jugadores() (+6 more)

### Community 22 - "constants.dart"
Cohesion: 0.08
Nodes (25): analizarCaptura, ApiConstants, AppConstants, appName, appVersion, authLogin, authMe, authRegistro (+17 more)

### Community 23 - "resolver_mercado.py"
Cohesion: 0.43
Nodes (6): Partido, Resuelve si una selección de cualquier mercado ganó o perdió, dado el resultado…, True si la selección ganó, False si perdió, None si no se puede resolver…, resolver_mercado(), _resultado_1x2(), _stats()

### Community 24 - "detalle_screen.dart"
Cohesion: 0.07
Nodes (29): ../../domain/usecases/get_detalle_partido.dart, ../../domain/usecases/get_prediccion_en_vivo.dart, _autoRefresh, build, _cargando, _cargar, child, createState (+21 more)

### Community 25 - "partidos_provider.dart"
Cohesion: 0.14
Nodes (13): ../../domain/usecases/get_partidos_hoy.dart, _cargando, cargarPartidosHoy, _error, _fecha, _getPartidosHoy, _ligaFiltro, ligasDisponibles (+5 more)

### Community 26 - "simular_jugadores_partido"
Cohesion: 0.29
Nodes (9): calcular_forma_jugador(), obtener_titulares_probables(), Session, Jugadores titulares en al menos min_apariciones (40% default) de los últimos…, Promedio de stats del jugador en sus últimos n partidos disputados antes de…, Simulación Monte Carlo de mercados individuales de jugador — tiros, tiros al…, Simula mercados individuales para el XI de ambos equipos. Usa la alineación…, simular_jugador() (+1 more)

### Community 27 - "job_crear_fixtures_sofascore.py"
Cohesion: 0.21
Nodes (10): buscar_candidatos(), equipos_de_la_liga(), Query base de equipos, acotada a los que ya jugaron en esta liga (evita que la…, Devuelve [(Equipo, score), ...]. score=None si vino de un sofascore_id ya…, correr_job_crear_fixtures_sofascore(), _parsear_temporada(), Crea Partido/Equipo desde Sofascore para temporadas que API-Football no puede…, 25/26" -> 2025 | "2025" -> 2025 | "Apertura 2025" -> 2025 | "Clausura 2026" ->… (+2 more)

### Community 28 - "stats_provider.dart"
Cohesion: 0.17
Nodes (11): bool get, ../../data/repositories/partido_repo_impl.dart, ../../domain/usecases/get_stats_modelo.dart, StatsModeloModel, StatsModelo, _cargando, cargar, _error (+3 more)

### Community 29 - "test_alineaciones.py"
Cohesion: 0.20
Nodes (15): EstadisticaJugador, obtener_lineup_confirmada(), Features a nivel jugador — para los mercados individuales (tiros, tiros al…, XI real confirmado por Sofascore para ESTE partido (job_alineaciones.py lo trae…, _equipo_temporal(), _limpiar(), _partido_temporal(), Bug real encontrado en sesión: Endrick (ya no juega en Lyon) seguía apareciendo… (+7 more)

### Community 30 - "stats_screen.dart"
Cohesion: 0.15
Nodes (16): ChangeNotifier, AppColors, StatsProvider, build, c, color, createState, initState (+8 more)

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

### Community 35 - "main.dart"
Cohesion: 0.18
Nodes (11): core/router.dart, _auth, BetMLApp, _BetMLAppState, build, createState, main, _router (+3 more)

### Community 36 - "failures.dart"
Cohesion: 0.39
Nodes (7): Failure, mensaje, NetworkFailure, NotFoundFailure, ParseFailure, ServerFailure, statusCode

### Community 37 - "recomendadas.dart"
Cohesion: 0.05
Nodes (45): ../../domain/entities/recomendadas.dart, ApuestaIndividualModel, CombinadaMismoPartidoModel, fromJson, MercadoCombinadaModel, ParlaySugeridoModel, PataParlayModel, RecomendadasModel (+37 more)

### Community 38 - "router.dart"
Cohesion: 0.10
Nodes (19): clay.dart, buildRouter, AppBottomNav, AppTab, build, current, _item, package:go_router/go_router.dart (+11 more)

### Community 39 - "parlay_screen.dart"
Cohesion: 0.08
Nodes (28): ../../data/datasources/parlay_remote_ds.dart, PartidosProvider, build, initState, build, _calculando, _calcular, createState (+20 more)

### Community 40 - "auth_remote_ds.dart"
Cohesion: 0.10
Nodes (22): ../auth_storage.dart, Client, ../../core/constants.dart, dart:convert, AuthClient, _inner, send, AnalisisImagenRemoteDataSource (+14 more)

### Community 41 - "login_screen.dart"
Cohesion: 0.10
Nodes (23): Color, ../../data/datasources/auth_remote_ds.dart, AuthProvider, build, _campo, createState, dispose, _emailCtrl (+15 more)

### Community 42 - "package:flutter/material.dart"
Cohesion: 0.09
Nodes (21): ../../core/theme.dart, dart:math, build, ConfidenceDial, ConfidenceMeter, label, size, value (+13 more)

### Community 44 - "modelos.py"
Cohesion: 0.11
Nodes (28): startup(), Base, crear_tablas(), Equipo, EstadisticaPartido, Liga, Partido, datetime (+20 more)

### Community 49 - "mis_predicciones_screen.dart"
Cohesion: 0.09
Nodes (23): ../../domain/usecases/get_predicciones_mias.dart, PrediccionesDePartido, actual, build, _cargando, _cargar, createState, _error (+15 more)

### Community 53 - "recomendadas_screen.dart"
Cohesion: 0.08
Nodes (25): ../../domain/usecases/get_recomendadas.dart, build, _cargando, _cargar, color, _CombinadasTab, createState, _dato (+17 more)

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
Cohesion: 0.08
Nodes (35): LigaSofascoreTorneo, Ids de torneo de Sofascore aprendidos para una liga nuestra. Una liga nuestra…, ahora_partidos(), Ahora" en la misma zona horaria naive que Partido.fecha — pipeline_dia.py pide…, filtrar_candidatos(), _parecido(), Encuentra el id de torneo de Sofascore de una liga nuestra cuando…, True si comparten alguna palabra significativa (por raíz, para que 'Friendlies'… (+27 more)

### Community 64 - ".predecir"
Cohesion: 0.14
Nodes (15): generar_resumen(), generar_resumen_h2h(), Por qué el modelo predijo lo que predijo — sin llamar a un LLM en cada request…, estimar_fraccion_restante(), Fracción del partido que falta jugar (0-1), para escalar el xG pre-partido en…, Partido, Recalcula 1X2 y mercados de gol EN VIVO dado el marcador y minuto actuales — no…, Genera lista de mercados recomendados según las probabilidades del modelo. Solo… (+7 more)

### Community 71 - "PartidoService"
Cohesion: 0.22
Nodes (8): PartidoService, Session, Lógica de negocio relacionada a partidos. Ensambla los datos de múltiples…, Convierte un objeto Partido en dict con datos relacionados. con_prediccion=True…, test_get_detalle_incluye_nombres_reales_no_ids(), test_get_detalle_partido_inexistente_devuelve_none(), test_get_partidos_hoy_cada_fila_trae_clave_prediccion(), _un_partido()

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
Cohesion: 0.09
Nodes (22): API (backend/api/) — endpoints nuevos/cambiados esta sesión, Arquitectura completa — qué existe y dónde, Backend — alineaciones/plantillas actualizadas, Backend — amistosos (Friendlies) visibles sin contaminar forma, Backend — ML / explicabilidad, Backend — otros bugs reales arreglados, Backend — reentreno diario, Backend — tab "Recomendadas" (feature nueva de hoy) (+14 more)

### Community 76 - "parlay.dart"
Cohesion: 0.14
Nodes (13): bankroll, cuotaCombinada, esValueBet, ev, mercado, parlayId, ParlaySeleccionInput, partidoId (+5 more)

### Community 77 - "auth_provider.dart"
Cohesion: 0.15
Nodes (12): ../../core/auth_storage.dart, autenticado, _autenticar, _cargando, _cargarSesion, _dataSource, _error, login (+4 more)

### Community 78 - "job_partidos_en_vivo.py"
Cohesion: 0.23
Nodes (15): correr_job_partidos_en_vivo(), _hay_algo_para_actualizar(), _necesita_actualizacion(), datetime, Refresca marcador/estado de los partidos de HOY mientras se juegan, y cierra…, Lógica pura (sin DB) — separada para poder testearla sin que partidos reales de…, correr_pipeline(), _partido() (+7 more)

### Community 79 - "job_odds_en_vivo.py"
Cohesion: 0.13
Nodes (18): Odds, Cuotas reales de casas de apuestas — API-Football /odds (gratis por fixture_id,…, Lectura de cuotas guardadas por job_odds.py — mejor cuota disponible por…, correr_job_odds(), correr_job_odds_en_vivo(), _hay_partidos_en_vivo(), Job de cuotas EN VIVO — GET /odds/live (gratis en el plan actual, verificado en…, _linea_a_clave() (+10 more)

### Community 80 - "partido_remote_ds.dart"
Cohesion: 0.17
Nodes (11): _client, _get, getDetalle, _getList, getPrediccionEnVivo, getPrediccionesHoy, getPrediccionesMias, getRecomendadas (+3 more)

### Community 81 - "api_client.py"
Cohesion: 0.27
Nodes (6): _fecha_hoy(), get_estadisticas_equipo(), get_fixtures_hoy(), get_h2h(), get_standings(), main()

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

### Community 98 - "predicciones_recomendadas"
Cohesion: 0.47
Nodes (5): predicciones_recomendadas(), Escanea TODOS los partidos de HOY con predicción + cuotas guardadas y arma tres…, correr_job_guardar_recomendadas(), Guarda las apuestas recomendadas del día para que se cierren solas contra el…, _ya_guardada()

### Community 99 - "encoger"
Cohesion: 0.33
Nodes (5): encoger(), medias_globales(), Medias globales de córners/tarjetas y encogimiento hacia ellas. Por qué existe:…, Promedios por partido y por localía. Se calculan una vez por proceso — son de…, Mezcla el promedio del equipo con la media global. Sin muestra devuelve la…

### Community 100 - "deploy_betml.py"
Cohesion: 0.47
Nodes (5): archivos_a_subir(), main(), mkdir_p(), Sube BetML Pro al servidor y reconstruye los contenedores. Mismo patrón que el…, Crea los directorios que falten, pero SOLO por debajo de REMOTO. Recorrer desde…

### Community 101 - "_Handler"
Cohesion: 0.40
Nodes (3): _Handler, main(), Túnel SSH a la base de producción, para desarrollar en local contra los datos…

### Community 102 - "construir_grafo"
Cohesion: 0.40
Nodes (4): construir_grafo(), Construcción del grafo equipo-jugador para la GNN. Dos tipos de nodo (equipo,…, Devuelve (grafo, id_a_indice_equipo, id_a_indice_jugador). fecha_corte=None usa…, HeteroData

### Community 103 - "calibracion_produccion.py"
Cohesion: 0.50
Nodes (4): cargar(), probabilidad_realista(), Calibración medida en PRODUCCIÓN — con las predicciones que ya se cerraron…, Corrige una probabilidad con lo observado en producción. Sin datos suficientes…

### Community 104 - "migrar_bd.py"
Cohesion: 0.50
Nodes (3): _db_url_local(), dump_local(), Copia la base local al Postgres de producción (una sola vez, para arrancar con…

## Knowledge Gaps
- **524 isolated node(s):** `Config`, `XCTest`, `AuthStorage`, `_claveToken`, `_storage` (+519 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_post` connect `predicciones.py` to `auth_remote_ds.dart`, `test_auth.py`?**
  _High betweenness centrality (0.425) - this node is a cross-community bridge._
- **Why does `guardar_mercados()` connect `predicciones.py` to `simular_partido`, `PrediccionRepository`, `PartidoRepository`?**
  _High betweenness centrality (0.141) - this node is a cross-community bridge._
- **Why does `apuesta_combinada()` connect `predicciones.py` to `PrediccionRepository`, `simular_partido`, `PartidoRepository`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `Partido` (e.g. with `Base` and `CodificadorTemporal`) actually correct?**
  _`Partido` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `PartidoRepository` (e.g. with `GuardarMercadosRequest` and `ParlayRequest`) actually correct?**
  _`PartidoRepository` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `PrediccionRepository` (e.g. with `GuardarMercadosRequest` and `ParlayRequest`) actually correct?**
  _`PrediccionRepository` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Config`, `XCTest`, `AuthStorage` to the rest of the system?**
  _524 weakly-connected nodes found - possible documentation gaps or missing edges._