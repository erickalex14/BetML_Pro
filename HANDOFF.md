# BetML Pro — Estado al 2026-08-13

App de predicciones de fútbol con ML. **Beta 0.1.0 desplegada y en uso.**
Este doc + el grafo de graphify (`graphify-out/`) son la forma de
retomar el proyecto sin releer el historial.

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

---

## 3. Agenda del scheduler

```
cada 15 min → alineaciones confirmadas (Sofascore, gratis)
cada 15 min → EN VIVO Sofascore: marcador/estado/minuto + stats + jugadores
cada 2 h    → red de seguridad API-Football (partidos sin anclar)
23:55 → fixtures de hoy          00:30 → estadísticas (tope 70 requests)
00:45 → fixtures de mañana       01:00 → Sofascore diario
01:15 → cuotas (tope 20)         01:30 → cerrar predicciones
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

---

## 4. Cómo aprende el modelo (importante, hubo confusión)

El reentreno diario aprende de **partidos terminados**, no de las
predicciones. Un partido entra al dataset con o sin predicciones
guardadas — el resultado ES la etiqueta. Que dos personas usen la app
**no entrena más el modelo**.

Lo que sí aportan las predicciones cerradas es la **calibración de
producción** (`backend/models/calibracion_produccion.py`): compara la
probabilidad declarada contra la frecuencia real de acierto. Si
declaramos 85% y acertamos 27%, Kelly viene recomendando stakes más
altos de lo que corresponde — y eso es plata. Se reajusta en el
reentreno diario y sale en `/stats/modelo` como `calibracion_real`.
Necesita 150 predicciones cerradas para activarse.

Las recomendadas se guardan solas (job 01:45) y se cierran contra el
resultado real, así que ese circuito ya está cerrado.

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

---

## 7. Arquitectura

**Pipeline** (`backend/pipeline/`): `pipeline_dia`, `job_estadisticas`,
`job_odds`, `job_odds_en_vivo`, `job_partidos_en_vivo`,
`job_cerrar_predicciones`, `job_guardar_recomendadas`,
`job_reentrenar_modelos`, `presupuesto.py`, y `sofascore/`
(`job_sofascore`, `job_historico_sofascore`, `job_alineaciones`,
`job_sofascore_en_vivo`, `descubridor_torneos`, `cliente` con Playwright).

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

**Tests:** 73, `.venv\Scripts\python.exe -m pytest tests/ -q`.
**Frontend:** `flutter analyze` → 0 issues.

---

## 8. Pendientes

- [ ] Verificar qué guarda realmente `rojas_local` (ver punto 5).
- [ ] Subir cobertura de anclaje de 24/33 (ver punto 6).
- [ ] Decidir si borrar el usuario de prueba `beta@gmail.com` de la BD
      de producción (se creó para verificar el login).
- [ ] Leeds vs Man United y Boise vs Sporting San José quedaron sin
      resultado: **ninguna de las dos fuentes los publicó**. Con la red
      de seguridad cada 2 h se llenan cuando alguna los tenga.
- [ ] El usuario mencionó querer Sofascore cada 20 min en vez de 15
      (hoy está en 15).
- [ ] Nada de HTTPS interno: el APK habla HTTPS con nginx, pero el
      contenedor escucha en 0.0.0.0:8010 sin TLS. En la red del server
      es aceptable; si algún día se expone el puerto directo, no.
