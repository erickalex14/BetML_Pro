# BetML Pro — handoff operativo (2026-08-14)

App móvil de predicciones de fútbol con ML, desplegada en producción y con APK distribuido.
Las Fases 0–3 del plan de endurecimiento están implementadas y verificadas. La primera entrega
del rediseño UX/UI móvil y su pulido 0.3.0 están desplegados en producción.

Este documento y `graphify-out/` son la entrada para retomar el proyecto sin releer el chat.
El plan aprobado vive en:
`C:\Users\USER\.claude\plans\twinkling-bouncing-blum.md`.

## 1. Estado actual

### Calidad de prediccion + APK 0.4.2 (14/08/2026)

- Eliminado el falso "sin historial" cuando hay al menos 3 partidos
  generales por equipo pero faltan 3 en la localia exacta: se usa fallback
  temporal a los ultimos 10 finalizados, siempre anteriores al encuentro.
- El fallback queda marcado como calidad `moderada` y sus probabilidades se
  contraen 15% hacia el prior neutral; con menos de 3 generales se bloquea.
- API expone codigo, calidad y conteos de historial; Detalle explica la causa
  real en lugar de mostrar un mensaje generico.
- Auditoria real: Al-Hilal Saudi FC (`sofascore_id=21895`) tiene 102 partidos
  finalizados en produccion (51 local, 51 visita), por lo que no corresponde
  clasificarlo como equipo sin historial.
- Verificacion: `108 passed`, `flutter analyze` limpio, API publica sana.
- APK: `https://novitec.com.ec/betml-apk/betml-pro-0.4.2.apk` y alias latest.
- SHA-256: `74ec2ce4a6916c9c38e2dce079ec28d2bcc2570d94221979508b5528940b0def`.

### Hotfix móvil 0.4.1 (14/08/2026)

- Todas las aperturas de Detalle usan `push`; las pantallas secundarias
  tienen `PopScope` con fallback seguro para el gesto Android.
- Radar del Home incluye carrusel horizontal de los mercados con mayor
  probabilidad del día y explicación al tocar.
- Filtros de Oportunidades usan el mismo lenguaje visual que ligas en Home.
- Constructor de parlay carga bajo demanda todos los mercados con cuota de
  cada partido, guarda el resultado y muestra probabilidad, cuota, Kelly y EV.
- `flutter analyze` limpio, `8/8` pruebas.
- APK: `https://novitec.com.ec/betml-apk/betml-pro-0.4.1.apk`.
- SHA-256: `e2d3399dbe51b338748954f1cee7863907cadb44c86d3bff43feca49959f1f24`.

### Release móvil 0.4.0 (14/08/2026)

- Política global de Atrás: tabs secundarias vuelven a Hoy; en Hoy se
  requieren dos gestos en dos segundos para salir.
- Oportunidades agrupadas por partido con logos, mercados desplegables,
  filtros por liga/estado y separación FIJA/SOÑADORA.
- Oportunidades se actualiza cada 60 segundos y al volver del segundo plano.
- Acceso a Crear parlay desde Home y Oportunidades; acceso a análisis de
  jugadores desde cada partido agrupado.
- API de recomendadas añade logos, liga_id y hora sin romper consumidores.
- Backend `106 passed`; Flutter `flutter analyze` limpio y `8/8` pruebas.
- APK: `https://novitec.com.ec/betml-apk/betml-pro-0.4.0.apk`.
- SHA-256: `bdac3f5a64eb9215da922e96ce09b7af9b5fe8d06909c711997e37d80d6fff86`.
- Pendiente deliberado: persistir recomendaciones de jugador requiere cuotas
  reales de jugador; hoy el endpoint entrega probabilidades, no EV verificable.

| Fase | Estado | Resultado principal |
|---|---|---|
| 0 — red de seguridad | Producción | tests aislados, backups verificados, límites Docker |
| 1 — seguridad | Producción | rate limiting, límites de payload/cómputo, CORS/JWT endurecidos |
| 2 — autenticación | Producción | Google Sign-In, access/refresh, rotación y logout |
| 3 — rendimiento | Producción | índices, caché PostgreSQL, gzip, joinedload y 3 workers |
| 4A — UX/UI móvil | Producción | navegación de 4 tabs, sistema deportivo, flujo principal y onboarding |
| 4A.1 — pulido móvil | Producción | Atrás seguro, UTF-8 limpio y ficha profesional de jugador |
| 4B — observabilidad | Pendiente | health real de DB, request timing, salud de jobs |

Validación más reciente:

- Backend: `106 passed` contra SQLite aislada.
- Flutter: `flutter analyze` sin problemas, 7 pruebas y APK release 0.3.0 compilado.
- APK: `https://novitec.com.ec/betml-apk/betml-pro-0.3.0.apk` y alias
  `https://novitec.com.ec/betml-apk/betml-latest.apk` (HTTP 200, 55.535.678 bytes).
- SHA-256: `7820bdb6f9026cf8e92648c8edde5a89d187b21df39d314f0d66b2069c3eb286`.
- Login Google validado manualmente en el APK productivo.
- Carga: 200 requests a `/partidos/hoy`, concurrencia 20, `200/200` HTTP 200 en 1.845 ms.

## 2. Producción y despliegue

- API: `https://novitec.com.ec/betml`
- APK estable actual: `https://novitec.com.ec/betml-apk/betml-pro-0.2.0.apk`
- APK latest: `https://novitec.com.ec/betml-apk/betml-latest.apk`
- Servidor: `181.198.104.181`, SSH `27619`, usuario `novitecadmin`
- Stack: `/home/novitecadmin/betml-stack/betml-pro`

| Contenedor | Función | Límites |
|---|---|---|
| `betml-api` | FastAPI/Uvicorn, 3 workers | 2 GiB, 2 CPU |
| `betml-scheduler` | jobs programados | 4 GiB, 2 CPU |
| `betml-db` | PostgreSQL 18 | 2 GiB, 2 CPU |

El nginx de aaPanel enruta `/betml/` a `127.0.0.1:8010` y sirve `/betml-apk/`.
Ese archivo comparte dominio con otras apps: respaldar y ejecutar `nginx -t` antes de recargar.

Despliegue:

```powershell
& '.\.venv\Scripts\python.exe' '.\deploy\deploy_betml.py'
```

`deploy_betml.py` exige credenciales por variables `BETML_SSH_*`, valida que JWT no use el
secreto default, crea un `pg_dump` verificable en `backups-predeploy/`, sube sin `.env`,
reconstruye y espera `/health`. Su lectura SSH combina stdout/stderr para evitar el bloqueo
que ocurrió durante Docker Build el 14/08.

Compilar APK:

```powershell
cd frontend
flutter build apk --release `
  --dart-define=API_BASE_URL=https://novitec.com.ec/betml `
  --dart-define=GOOGLE_CLIENT_ID=<web-client-id>.apps.googleusercontent.com
```

El APK actual conserva la firma debug del APK distribuido para permitir actualización encima.
Antes de distribución masiva/Play Store hay que definir una clave release estable y gestionar
la transición; cambiar la firma impide instalar encima sin desinstalar.

## 3. Red de seguridad y pruebas

`tests/conftest.py` requiere `BETML_TEST_DB_URL`. Pytest aborta si falta o si apunta al mismo
destino que `DB_URL`. PostgreSQL usa un schema separado; SQLite sirve para la suite rápida.

```powershell
$env:BETML_TEST_DB_URL='sqlite:///data/betml_test_local.db'
rtk test '.\.venv\Scripts\python.exe' -m pytest -q
```

Nunca ejecutar tests con el `.env` normal dando por hecho que es local: ese archivo puede
apuntar al túnel de producción.

Backups:

- predeploy: `backups-predeploy/betml-YYYYMMDD-HHMMSS.dump`
- scheduler diario: 04:30, `backend/pipeline/job_backup.py`
- `pg_dump`/`pg_restore` son versión 18 y el dump se valida antes de aceptarse.

## 4. Autenticación y seguridad

Google OAuth usa un cliente Android (`com.betmlpro.frontend` + SHA-1 de la firma actual) y
un cliente Web como audiencia del backend. `GOOGLE_CLIENT_ID` vive en el `.env` remoto.
No guardar secretos OAuth en el repo; el Client ID no es secreto.

Flujo:

- Access JWT: 15 minutos, `type=access`, `iat` y `exp`.
- Refresh JWT: 30 días; solo se guarda SHA-256 en `sesiones_refresh`.
- `/auth/refresh` rota el refresh. Reutilizar uno revocado invalida todas las sesiones del usuario.
- `/auth/logout` revoca la sesión.
- Google solo une cuentas por email cuando `email_verified=true`.
- Usuarios Google pueden tener `password_hash=NULL`; login password responde que deben usar Google.
- Compatibilidad temporal: JWT antiguos sin `type` siguen aceptándose como access. El APK viejo,
  identificado por no enviar `X-BetML-Auth-Version: 2`, recibe access de 7 días hasta retirarlo.

Seguridad Fase 1:

- rate limit global 300/min por IP; login/registro 5/min; captura/combinada 10/min por usuario/IP;
- parlay máximo 12 patas; límites de bankroll/fracción/mercados;
- imágenes hasta 5 MiB, MIME validado y lectura por streaming;
- CORS allowlist; JWT default bloquea startup en producción;
- excepciones 500 no filtran detalles y entregan correlation ID.

## 5. Rendimiento medido

Fase 3 se decidió con datos de producción, no estimaciones:

- Tabla `partidos`: 17.647 filas al medir.
- Día 14/08: 36 partidos; 13 con cuotas.
- `/recomendadas` frío antes: 1.682 ms.
- Después: 905 ms frío y 3,6 ms caliente (~467×).
- Consulta diaria: `Seq Scan` 1,478 ms → `Index Scan` 0,128 ms (~11,5×).
- GZip confirmado por `content-encoding: gzip`.

`cache_json` es PostgreSQL/JSONB, compartido entre workers:

- `recomendadas:{fecha}`: TTL 30 min;
- `partidos_hoy:{fecha}`: TTL 5 min;
- job 01:45 precalienta recomendadas;
- actualizaciones en vivo invalidan ambas claves.

Los parámetros no-default de `/recomendadas` omiten el caché para no devolver resultados de
otro bankroll/fracción/número de simulaciones.

Índices: fecha/estado/liga/equipos de `Partido`; `partido_id` en Odds y Predicción;
partido/equipo/jugador en EstadísticaJugador; compuestos `(equipo_local_id, fecha)` y
`(equipo_visit_id, fecha)`. `joinedload` elimina el N+1 de partidos/equipos/liga/stats.

Los artefactos `calibracion.pkl` y `rho_dixon_coles.pkl` se cachean por `mtime`; un reentreno
se detecta sin reiniciar la API. Cada worker tiene pool 8 + overflow 4; PostgreSQL permite 100.

## 6. Fechas y partidos “de hoy”

`Partido.fecha` se guarda UTC-naive. El día visible es `America/Guayaquil`, convertido a rango
UTC semiabierto. Ejemplo: 14/08 Ecuador = `[2026-08-14 05:00, 2026-08-15 05:00)` UTC.

Bug corregido: Cienciano–Botafogo y Rosario Central estaban a `00:30 UTC` del 14/08, pero eran
19:30 Ecuador del 13/08. El filtro anterior por calendario UTC los mostraba al día siguiente.
También se corrigió el scheduler 23:55, que calculaba “mañana” desde UTC y podía saltar fecha.

No volver a filtrar `Partido.fecha` con strings `00:00–23:59`; usar
`rango_utc_dia_partidos()` y `fecha_hoy_partidos()`.

## 7. Scheduler de producción

```text
cada 15 min  alineaciones confirmadas Sofascore
cada 15 min  marcador/stats/jugadores en vivo Sofascore
cada 2 h     red de seguridad API-Football
23:55        fixtures de hoy + mañana
00:30        estadísticas API-Football
00:45        fixtures de mañana
01:00        Sofascore diario
01:10        cuotas en cascada
01:30        cerrar predicciones
01:45        guardar y precalentar recomendadas
03:00        reentrenar XGBoost/MLP/LSTM/GNN + Dixon-Coles
04:30        pg_dump verificado
```

API-Football tiene 100 requests/día, reset UTC, controlado por `presupuesto_api_football`.
Sofascore maneja el vivo. `job_odds_en_vivo` existe pero no está agendado porque excedía cuota.

## 8. Modelo y calibración

El entrenamiento aprende de partidos terminados; las predicciones de usuarios no son etiquetas
de entrenamiento. Predicciones cerradas del sistema y usuarios sí alimentan
`calibracion_produccion.py`, por familia de mercado, antes de Kelly.

No confiar en cifras plausibles sin medir. Caso real: corners Over 11.5 parecía 85%, pero la
frecuencia sobre 15.689 partidos era 27,1%. Se corrigió con regresión a la media (`K=8`).

Pendiente crítico: no apostar mercados de rojas. `rojas_local/visitante` de Sofascore tiene
promedios irreales (~0,52) y falta verificar el payload crudo.

## 9. Trampas conocidas

- Puerto 8001 pertenece a `novitec-sgn`; BetML usa 8010.
- Postgres 18 monta `/var/lib/postgresql`, no `/var/lib/postgresql/data`.
- API y scheduler necesitan `TZ=America/Guayaquil`.
- El scheduler corre solo en servidor; no levantar otro contra la misma cuota.
- `torch==2.13.0+cpu` requiere el índice de PyTorch del Dockerfile.
- El `.env` de producción no se sube.
- El servidor aloja otras apps; conservar límites y medir antes de aumentar workers/CPU/RAM.
- `rtk` es 0.42.4; en sesiones aisladas puede requerir `CLAUDE_CONFIG_DIR=C:\Users\USER\.claude`.
- El intérprete de graphify está registrado en `graphify-out/.graphify_python`; usarlo para
  `python -m graphify update .` si el trampoline `graphify.exe` falla.

## 10. Rediseño UX/UI móvil

Primera entrega implementada el 2026-08-14, todavía no desplegada:

- Navegación inferior: Hoy, Oportunidades, Portafolio y Rendimiento; Perfil queda en el avatar.
- Rutas nuevas `/oportunidades`, `/portafolio` y `/rendimiento`; las rutas históricas siguen válidas.
- Modo oscuro por defecto, superficies planas y tokens azul/verde/naranja/rojo con semántica estable.
- Login explica ML/Monte Carlo, Kelly y seguimiento sin prometer resultados.
- Home prioriza radar del día y oportunidad destacada; Detalle separa resumen, modelo, mercado y contexto.
- Oportunidades usa riesgo controlado/alto; Portafolio agrupa selecciones y abre constructor combinado.
- Rendimiento separa explícitamente métricas globales del modelo de la actividad del usuario.
- Eventos UX pasan por `ProductAnalytics`; actualmente solo se imprimen en debug y no envían PII.
- Validación local: `flutter analyze` limpio, `flutter test` 5/5 y
  `frontend/build/app/outputs/flutter-apk/app-debug.apk` generado.

Pendiente UX: prueba manual en Android pequeño/grande, golden baselines, proveedor de analítica con
consentimiento, medición real de Home <2 s y APK release firmado.

APK 0.2.0+2 publicado el 2026-08-14 con firma debug compatible con la versión distribuida.
El script `deploy/deploy_apk.py` publica atómicamente en `/home/novitecadmin/betml-stack/apk`,
verifica SHA-256 y actualiza `betml-latest.apk` sin borrar versiones anteriores.

Cupón de predicciones publicado el 2026-08-17 en APK `0.4.7+11`:

- `PredictionCouponProvider` conserva hasta 30 selecciones al navegar entre pestañas.
- La burbuja sobre la navegación abre un bottom sheet para quitar, vaciar, copiar y analizar.
- No hay importes ni dinero: muestra mercado, probabilidad del modelo y contexto del partido.
- El mismo cupón recibe selecciones desde el constructor, recomendaciones individuales,
  recomendaciones de jugadores y mercados del detalle del partido.
- Los mercados de jugadores solicitan cuota decimal informativa antes de agregarse.
- El análisis/guardado sigue usando el endpoint de parlay existente y termina en Portafolio.
- Límite deliberado actual: una selección por partido; elegir otra reemplaza la anterior.
- Validación local: `flutter analyze` limpio y 11 pruebas Flutter aprobadas, incluida la
  transición agregar/reemplazar/quitar del proveedor.
- Descarga versionada: `https://novitec.com.ec/betml-apk/betml-pro-0.4.7%2B11.apk`.
- Descarga latest: `https://novitec.com.ec/betml-apk/betml-latest.apk`.
- APK: 56.044.030 bytes; SHA-256
  `b6bb9b1d303e8fe4074db10e748acf57b2d9ee2fbd2972295a6a6650ab302190`.

## 11. Pendientes priorizados

1. Probar el cupón del APK `0.4.7+11` en Android real y permitir varias selecciones del mismo
   partido cuando el backend modele su correlación.
2. Fase 4B: `/health` con `SELECT 1` y 503, healthcheck API, request-id/latencia, salud de jobs.
3. Verificar el campo de tarjetas rojas contra payload Sofascore real.
4. Mejorar anclaje `sofascore_id` de torneos/amistosos faltantes.
5. Mejorar matching de odds-api.io (`KuPS` vs `Kuopion Palloseura`).
6. Corregir partidos Saudi Pro League sin historial/predicción.
7. Definir firma Android release estable antes de publicación masiva.
8. Revisar por qué el home no mostró recomendaciones una vez; ahora el endpoint produce 30 y
   tiene caché, pero falta reproducir el flujo visual si vuelve a ocurrir.
9. Considerar Alembic cuando haya otra ronda de cambios de esquema; hoy
   `backend/db/migraciones.py` usa ALTER/CREATE INDEX idempotentes.

## 12. Prompt para retomar

> Retomamos BetML Pro. Lee `HANDOFF.md`, el plan aprobado en
> `C:\Users\USER\.claude\plans\twinkling-bouncing-blum.md` y usa `graphify-out/` para navegar.
> Fases 0–3 están desplegadas; Fase 4A y el cupón global están publicados en APK `0.4.7+11`.
> Continúa con validación Android y luego Fase 4B de observabilidad. Usa `rtk`, ejecuta tests solo
> con `BETML_TEST_DB_URL`, preserva el árbol sucio y verifica números contra producción antes
> de cambiar recursos o lógica. El servidor comparte carga con otras aplicaciones.
