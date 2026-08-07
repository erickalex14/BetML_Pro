import time
import logging
from backend.pipeline.sofascore.job_historico_sofascore import (
    correr_job_historico_sofascore
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)


def main():
    log.info("Iniciando carga completa histórica Sofascore")

    ronda = 1
    errores_consecutivos = 0

    while True:
        log.info(f"\n{'='*55}")
        log.info(f"  RONDA {ronda}")
        log.info(f"{'='*55}")

        try:
            # Sin límite: una pasada cubre todas las temporadas.
            # Las rondas solo existen para reintentar tras un error.
            correr_job_historico_sofascore()
            log.info(f"Ronda {ronda} OK — histórico completo")
            break

        except Exception as e:
            errores_consecutivos += 1
            log.error(f"Error en ronda {ronda}: {e}")
            log.info(
                f"Reinten+tando en 120 segundos... "
                f"(error {errores_consecutivos} consecutivo)"
            )

            # Si hay 5 errores seguidos → pausa larga
            if errores_consecutivos >= 5:
                log.warning("5 errores consecutivos — pausa de 10 minutos")
                time.sleep(600)
                errores_consecutivos = 0
            else:
                time.sleep(120)


if __name__ == "__main__":
    main()