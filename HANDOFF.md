# BetML Pro — Estado al 2026-08-13 (tarde)

App de predicciones de fútbol con ML. **Beta 0.1.0 desplegada y en uso.**
Este doc + el grafo de graphify (`graphify-out/`, 1760 nodos) son la
forma de retomar el proyecto sin releer el historial.

## LO PRIMERO SI RETOMÁS AHORA

Hay un **plan aprobado y sin empezar** para login con Google y
endurecimiento para miles de usuarios:
`C:\Users\USER\.claude\plans\twinkling-bouncing-blum.md`

Va por fases, ordenadas por "qué rompe primero": red de seguridad
(tests fuera de prod, backups, límites de Docker) → agujeros
explotables hoy → Google auth + refresh tokens → rendimiento →
observabilidad. Los números que lo justifican están medidos, no
supuestos.

**Las tres cosas más urgentes de ese plan**, por si solo hay tiempo
para eso:
1. `pytest` escribe en la **base de producción** (el `.env` de dev
   apunta ahí por el túnel). Ya se insertaron usuarios de prueba sin
   querer. Falta `tests/conftest.py`.
2. `ParlayRequest.selecciones` no tiene tope: 50 patas = 500.000
   simulaciones sincrónicas. Es un DoS con un solo request.
3. Los contenedores no tienen límite de RAM y el server corre otras
   apps de producción (`novitec-sgn`, `syserp`, `mba3-bi`).

---

## 1. PRODUCCIÓN — ya andando

**API pública:** `https://novitec.com.ec/betml`
**APK (mismo link siempre, se pisa al actualizar):**
`https://novitec.com.ec/betml-apk/betml-beta-0.1.0-e15954.apk`

**Server:** 181.198.104.181, SSH puerto 27619, usuario `novitecadmin`.
Stack en `/home/novitecadmin/betml-stack/betml-pro`:

| contenedor | qué es | puerto |
|---|---|---|
| `betml-api` | FastAPI | 0.0.0.0:8010 → 8001 |
| `betml-scheduler` | jobs agendados | — |
| `betml-db` | Postgres 18 | 127.0.0.1:5434 (no expuesta a internet) |

El nginx de aaPanel (`/www/server/panel/vhost/nginx/novitec.com.ec.conf`)
enruta `/betml/` al contenedor y `/betml-apk/` al APK como archivo
estático. Mismo patrón que `/sgn` y `/reportesmba`. El `proxy_pass` con
barra final corta el prefijo, así que la API no sabe que vive bajo un
subpath. **Ese archivo sirve varias apps en producción**: tocarlo
siempre con respaldo + `nginx -t` antes de recargar.

```bash
# desplegar cambios (sube codigo y reconstruye contenedores)
MSYS_NO_PATHCONV=1 BETML_SSH_HOST=181.198.104.181 BETML_SSH_PORT=27619 \
BETML_SSH_USER=novitecadmin BETML_SSH_PASS=... \
BETML_REMOTE_DIR=/home/novitecadmin/betml-stack/betml-pro \
  .venv/Scripts/python.exe deploy/deploy_betml.py

# desarrollar en local contra la BD de PRODUCCION (dejar corriendo aparte)
BETML_SSH_HOST=... BETML_SSH_USER=... BETML_SSH_PASS=... BETML_SSH_PORT=27619 \
  .venv/Scripts/python.exe deploy/tunel_bd.py

# compilar APK (la URL se hornea en tiempo de build)
cd frontend && flutter build apk --release \
  --dart-define=API_BASE_URL=https://novitec.com.ec/betml
```

**El scheduler corre SOLO en el server.** No levantar el local a la vez:
comparten la misma cuota de 100 requests/día de API-Football.

**Ojo con el túnel:** el `.env` local apunta a la BD de producción, así
que cualquier script que corras en local **escribe en la base real**. El
`DB_URL` local viejo quedó comentado arriba en el `.env` por si querés
volver a trabajar aislado. El túnel además se cae bajo carga (un test
que abre 100 conexiones seguidas lo tumba) — si ves
`server closed the connection unexpectedly`, reinicialo.

---

## 2. Trampas de deploy — ya costaron tiempo, no repetirlas

- El puerto **8001 lo usa `novitec-sgn`** en ese server. BetML va en 8010.
- `torch==2.13.0+cpu` **no está en PyPI**; el Dockerfile agrega
  `--extra-index-url https://download.pytorch.org/whl/cpu`.
- La versión de Postgres del contenedor **debe coincidir** con la del
  `pg_dump` local (18), si no `pg_restore` rebota el dump por versión
  de formato.
- Postgres **18+ monta el volumen en `/var/lib/postgresql`**, no en
  `.../data`. Con el path viejo el contenedor arranca y se muere.
- Los contenedores necesitan **`TZ=America/Guayaquil`**: en UTC,
  `date.today()` adelanta el día (a las 19:00 de acá ya es mañana) y
  `schedule.at("03:00")` dispara 5 horas corrido.
- **Git Bash reescribe** rutas `/home/...` a `C:/Program Files/Git/home/...`
  — usar `MSYS_NO_PATHCONV=1` al pasar rutas remotas.
- SFTP **no puede leer archivos de root** (los de nginx): leerlos por
  `sudo base64` y escribirlos por `sudo tee`.
- **`Partido.fecha` está en UTC**, aunque `pipeline_dia` pida los
  fixtures con `timezone=America/Guayaquil`. Medido contra los
  `startTimestamp` de Sofascore: 8 de 8 partidos con 0.0 h de
  diferencia. `ahora_partidos()` devuelve UTC por eso. La app convierte
  a hora local del celular (`fecha` va marcada con "Z" y el modelo hace
  `.toLocal()`).
- **El túnel a la BD se cae bajo carga** (un test que abre 100
  conexiones lo tumba). Si ves `server closed the connection
  unexpectedly` en local, reiniciá `deploy/tunel_bd.py`.
- Correr scripts dentro del contenedor necesita `sys.path.insert(0,
  "/app")`, si no `ModuleNotFoundError: backend`.

---

## 3. Agenda del scheduler

```
cada 15 min → alineaciones confirmadas (Sofascore, gratis)
cada 15 min → EN VIVO Sofascore: marcador/estado/minuto + stats + jugadores
cada 2 h    → red de seguridad API-Football (partidos sin anclar)
23:55 → fixtures de hoy Y de mañana   00:30 → estadísticas (tope 45)
00:45 → fixtures de mañana            01:00 → Sofascore diario
01:10 → cuotas en cascada             01:30 → cerrar predicciones
01:45 → guardar recomendadas del día para seguimiento
03:00 → reentrenar los 4 modelos + Dixon-Coles + calibración de producción
```

**Presupuesto de API-Football: 100 requests/día**, reset a medianoche
**UTC**. Contador en la tabla `presupuesto_api_football`, dentro de
`api_client.get()` (choke point único, con corte duro al llegar a 100).
El vivo va por Sofascore porque no gasta cuota; API-Football quedó solo
para lo nocturno y la red de seguridad cada 2 h (~6 requests/día).
`job_odds_en_vivo` existe pero **no está agendado**: a 5 min pedía
~168/día, no entra.

**El job de las 23:55 baja hoy Y mañana a propósito.** Es redundante
con el de las 00:45, pero la agenda tenía un hueco de un día entero: si
el scheduler estaba caído en esa ventana, ese día se quedaba sin
partidos y nada lo recuperaba (pasó el 13/08, la app mostraba "no hay
partidos hoy"). Además `_necesita_actualizacion` devuelve True con la
lista vacía — antes era circular: sin partidos no había nada que
actualizar, y sin actualizar nunca había partidos.

---

## 3b. Cuotas — cascada de fuentes gratis

`backend/pipeline/odds/orquestador.py` (01:10). Cada fuente pide **solo
lo que la anterior no cubrió**:

| Orden | Fuente | Tope | Notas |
|---|---|---|---|
| 1 | **Sofascore** | sin tope | `/event/{id}/odds/1/all` (bet365). Cubre amistosos. Cuotas **fraccionarias** ("1/5" = 1.20) y la línea va en `choiceGroup` |
| 2 | **The Odds API** | 500/mes | 1 request = liga entera. **El costo es mercados × regiones**, no 1: con 2 mercados son ~8 ligas/día |
| 3 | **odds-api.io** | 500/día | `/v3/events` trae ~4600 partidos. **Betano tiene prioridad sobre Bet365** porque es donde apuesta el usuario |
| 4 | API-Football | 100/día | último recurso, se salta si quedan <40 |

Las keys viven en el `.env` (`THE_ODDS_API_KEY`, `ODDS_API_IO_KEY`) y
están declaradas en `core/config.py` — Settings **rechaza** claves del
`.env` que no conozca.

**Pendiente real:** odds-api.io cotizó 0 partidos porque el cruce de
nombres es muy estricto (`KuPS` vs `Kuopion Palloseura` puntúa 0.36).
Hay que aflojar el umbral o reusar la lógica de `_similitud` con la
regla de ventaja sobre el segundo candidato.

---

## 4. Cómo aprende el modelo (importante, hubo confusión)

El reentreno diario aprende de **partidos terminados**, no de las
predicciones. Un partido entra al dataset con o sin predicciones
guardadas — el resultado ES la etiqueta. Que dos personas usen la app
**no entrena más el modelo**.

Lo que sí aportan las predicciones cerradas es la **calibración de
producción** (`backend/models/calibracion_produccion.py`): compara la
probabilidad declarada contra la frecuencia real de acierto **por
familia de mercado**, y ese factor **se aplica en `analizar_mercados_kelly`
antes de calcular EV y stake**. Ahí es donde el sistema "aprende de sus
errores": si en córners venimos declarando 64% y acertando 10%, esos
mercados entran a Kelly con un 28% menos de confianza.

Cuenta **todas** las predicciones cerradas, del sistema y de los
usuarios, sin filtrar por dueño — el aislamiento entre cuentas es solo
de visibilidad. Con 10 usuarios hay 10 veces más señal.

Medición del 13/08 (43 cerradas): corners 64%→10% (factor 0.72),
goles 54%→43% (0.92), otros 43%→11% (0.77). Visible en `/stats/modelo`
bajo `calibracion_real.por_mercado`.

Tres decisiones de diseño, todas por la poca muestra: **por familia**
(el error de córners no dice nada del 1X2), **encogido hacia 1** con
`K_ENCOGIMIENTO=20` (8 observaciones no pueden mandar solas), y
**ventana móvil** — importante, porque el desastre de córners venía de
un bug ya arreglado y sin ventana el sistema lo castigaría para
siempre.

Las recomendadas se guardan solas (job 01:45) y se cierran contra el
resultado real, así que ese circuito ya está cerrado.

**Aislamiento entre usuarios** (`Prediccion.usuario_id`): con valor = la
guardó esa persona y solo ella la ve; NULL = la generó el sistema, no se
le muestra a nadie pero sí cuenta para las métricas. Las 58 predicciones
previas a la columna quedaron como del sistema — no había forma de saber
quién las hizo. **`Parlay` todavía NO tiene ese filtro** (está en la
Fase 1 del plan).

---

## 5. Bugs de correctitud encontrados (todos con test que los fija)

Los tres salieron de mirar la app, no de los tests. Vale la pena
desconfiar de números que "se ven plausibles":

1. **Córners inflados.** El modelo daba 85% al Over 11.5 cuando la
   frecuencia real en 15.689 partidos es 27.1% (la casa lo pagaba 3.80,
   o sea tenía razón). Causa: lambda del Poisson = promedio crudo de 5
   partidos, sin regresión a la media. Arreglo en
   `backend/features/medias_liga.py`, con K=8 elegido midiendo sobre 323
   partidos (sesgo −0.10, Brier 12% mejor). **Toda "fija" de córners era
   una apuesta perdedora.**
2. **Marcadores borrados.** `guardar_partido` pisaba el marcador que ya
   había traído Sofascore con los nulos de API-Football (que en
   amistosos chicos se queda en "NS" durante horas). Regla nueva: un
   partido terminado no vuelve a "por jugarse", y `None` significa "esta
   fuente no sabe", no "no hubo goles".
3. **Empate en vivo al 69%.** El xG de Sofascore en un partido en curso
   es lo ACUMULADO, y se trataba como previsión del partido completo
   multiplicándolo otra vez por el tiempo restante. Doble descuento.
   Ahora se extrapola el ritmo a 90 y se mezcla con la previsión
   pre-partido pesando por minutos jugados.

**PENDIENTE SIN RESOLVER — no apostar mercados de rojas.**
`rojas_local` en `estadisticas_sofascores` promedia 0.52 por equipo y
por partido en todos los años (2023-2026), cuando lo real ronda
0.05-0.10. Ese campo no está guardando tarjetas rojas. Falta verificar
contra el payload crudo de Sofascore qué es lo que trae.

---

## 6. Anclaje de `sofascore_id` — el cuello de botella

Sin `sofascore_id` un partido **no tiene marcador en vivo, ni alineación
confirmada, ni stats**. Cobertura hoy: **24 de 33** partidos del día.

El endpoint bueno es `/unique-tournament/{id}/scheduled-events/{fecha}`
(sacado del tráfico real de sofascore.com). Los que NO sirven, ya
probados: `/sport/football/scheduled-events/{fecha}` da 404 y
`/events/next/` también.

El cruce es por similitud de nombre eligiendo el **mejor** candidato del
torneo y la fecha. Hizo falta puntaje en vez de reglas rígidas porque
las dos fuentes escriben distinto el mismo club:
`RB Bragantino`/`Red Bull Bragantino`, `Atletico-MG`/`Atlético Mineiro`,
`Rapid Vienna`/`SK Rapid Wien`, `FC Copenhagen`/`FC København`. Y hace
falta **ventaja sobre el segundo candidato** porque hay equipos
distintos que puntúan altísimo (`Independiente` vs `Independiente del
Valle` da 1.00).

Para subir la cobertura: mapear los ids de torneo que faltan
(clasificaciones y el resto de los amistosos). El descubridor
(`descubridor_torneos.py`) los busca solo y guarda lo que aprende en
`liga_sofascore_torneo`, pero tiene topes (`MAX_PAGINAS=3`,
`MAX_CANDIDATOS=8`) que recortan.

### 6b. Equipos duplicados — revisar si aparecen otra vez

Un club quedaba cargado **dos veces** cuando entraba por dos caminos
(API-Football en una copa + Sofascore al importar su liga), porque
`buscar_candidatos` miraba solo equipos **de la liga que se estaba
importando**. Consecuencia grave: el partido apuntaba a la fila vacía
mientras el historial colgaba de la otra, y el modelo lo descartaba por
"historial insuficiente" (caso real: Mirassol vs LDU de Quito, sin
predicción teniendo 58 partidos en la fila duplicada).

Ya corregido (ahora cae a buscar en todas las ligas) y **fusionados 20
equipos** (Fluminense, Grêmio, Vasco, Bahia, Vitória…), 569 referencias
repuntadas. Si vuelve a pasar:
`python -m backend.pipeline.sofascore.fusionar_equipos --listar` para
ver qué haría, sin `--listar` para aplicarlo.

**Ligas que API-Football free no cubre** (solo llega a 2024): sus
temporadas 2026 se traen de Sofascore. Ya cargadas Brasileirão (87678),
MLS (86668), Liga Argentina (87913), LigaPro Ecuador (89674) y Liga MX
Apertura (96191) — 1016 partidos. Si otra liga aparece congelada,
buscar el season id en `/unique-tournament/{id}/seasons`, agregarlo a
`TEMPORADAS_HISTORICAS` y correr
`job_crear_fixtures_sofascore`.

**Decisión tomada:** los equipos de ligas que NO seguimos (checa,
polaca, sueca, suiza, segunda española) que aparecen en clasificatorias
o amistosos **se dejan sin predicción**. Eran 35 de 65 partidos. Se
escribió y descartó un job de relleno por equipo.

---

## 7. Arquitectura

**Pipeline** (`backend/pipeline/`): `pipeline_dia`, `job_estadisticas`,
`job_odds`, `job_odds_en_vivo`, `job_partidos_en_vivo`,
`job_cerrar_predicciones`, `job_guardar_recomendadas`,
`job_reentrenar_modelos`, `presupuesto.py`, `odds/` (orquestador en
cascada + `the_odds_api` + `odds_api_io`), y `sofascore/`
(`job_sofascore`, `job_historico_sofascore`, `job_alineaciones`,
`job_sofascore_en_vivo`, `job_odds_sofascore`, `descubridor_torneos`,
`fusionar_equipos`, `cliente` con Playwright).

**Modelos** (`backend/models/`): XGBoost + MLP + LSTM + GNN combinados en
`ensemble.py` (pondera por accuracy real). `montecarlo.py`
(Dixon-Coles), `kelly.py`, `kelly_portfolio.py`, `parlay.py`,
`calibracion.py`, `calibracion_produccion.py`, `explicacion.py`,
`jugadores_montecarlo.py`, `parser_imagen.py`, `resolver_mercado.py`.

**API** (`backend/api/routes/`): `partidos`, `predicciones`, `stats`,
`auth`. Todo bajo JWT excepto `/auth/*` y `/health`.

**Frontend** (`frontend/lib/`): arquitectura limpia
(domain/data/presentation), Provider, go_router. Pantallas: login, home,
detalle, análisis avanzado, recomendadas (fijas/soñadoras), mis
predicciones (agrupadas por partido con escudos), stats, perfil, parlay,
analizar-captura.

**Tests:** 96, `.venv\Scripts\python.exe -m pytest tests/ -q`.
**Frontend:** `flutter analyze` → 0 issues.

⚠️ **Los tests escriben en la base de PRODUCCIÓN.** 8 archivos usan
`SessionLocal` y el `.env` de dev apunta al server por el túnel. Ya se
insertaron usuarios de prueba sin querer. Los tests nuevos deberían ir
contra lógica pura hasta que exista `tests/conftest.py` (Fase 0 del
plan).

---

## 8. Pendientes

- [ ] **Ejecutar el plan aprobado** (ver arriba del todo).
- [ ] Verificar qué guarda realmente `rojas_local` (ver punto 5).
      **No apostar mercados de rojas hasta entonces.**
- [ ] Subir cobertura de anclaje de 24/33 (ver punto 6).
- [ ] odds-api.io cotiza 0 partidos: el cruce de nombres es muy
      estricto (ver punto 3b).
- [ ] Decidir si borrar los usuarios de prueba `beta@gmail.com` y
      `aislamiento@gmail.com` de la BD de producción.
- [ ] El usuario mencionó querer Sofascore cada 20 min en vez de 15
      (hoy está en 15).
- [ ] Los 3 partidos de **Saudi Pro League** sin predicción: esa liga
      SÍ la seguimos, así que ahí falta algo (¿temporada 2026?).

---

## 9. Prompt para retomar

Copiá esto en una sesión nueva:

> Retomamos BetML Pro. Leé `HANDOFF.md` en la raíz del repo y el plan
> aprobado en `C:\Users\USER\.claude\plans\twinkling-bouncing-blum.md`
> antes de tocar nada. También hay un grafo de graphify en
> `graphify-out/` (1760 nodos) que sirve para navegar el proyecto.
>
> La app está en producción en `https://novitec.com.ec/betml` con el
> APK repartido, y el plan es para abrirla a miles de usuarios: login
> con Google + refresh tokens, y tapar los agujeros que encontramos
> midiendo (DoS con un request, sin rate limiting, `/recomendadas` con
> 552.000 simulaciones por request y sin cache).
>
> Arrancá por la **Fase 0** del plan, que es la red de seguridad:
> `tests/conftest.py` para que pytest deje de escribir en la base de
> producción, backups con `pg_dump`, y límites de RAM/CPU en
> `docker-compose.prod.yml` (ojo: ese server corre otras apps de
> producción del usuario).
>
> Antes de dar algo por hecho, verificalo contra datos reales — en esta
> sesión varios números que "se veían plausibles" estaban mal (córners
> al 85% cuando la realidad era 27%).
- [ ] Nada de HTTPS interno: el APK habla HTTPS con nginx, pero el
      contenedor escucha en 0.0.0.0:8010 sin TLS. En la red del server
      es aceptable; si algún día se expone el puerto directo, no.
