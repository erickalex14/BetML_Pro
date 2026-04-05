backend/
  pipeline/
    config.py        ← lee el .env y centraliza la configuración
    api_client.py    ← se conecta a API-Football y trae datos
    test_conexion.py ← prueba que todo funcione

  pipeline/
    guardador.py     ← guarda los datos de la API en la BD
    pipeline_dia.py  ← orquesta todo: trae datos Y los guarda


Config.py:
Centraliza toda la configuración del proyecto en un solo lugar. En Spring esto sería tu clase @Configuration. 
La regla es: ningún otro archivo escribe strings de configuración directo — todos importan desde aquí.

api_client.py:
Es el único archivo que habla con API-Football. 
Todos los demás módulos del proyecto le piden datos a este — nunca hacen peticiones HTTP directas. 

test_conection.py
Prueba que todo funciona antes de construir el resto. Es tu primer test de integración real.

Arquitectura de los datos
23:55  → pipeline_dia.py
         Trae TODOS los partidos del día con estado final
         1 request → guarda resultados en BD
         ─────────────────────────────────────────────
00:30  → job_estadisticas.py
         Los partidos ya están FT en la BD
         Trae stats de hasta 20 partidos por ejecución
         Si hay más de 20, el job de mañana sigue
         ─────────────────────────────────────────────
Diario → modelo se nutre solo con datos nuevos cada día