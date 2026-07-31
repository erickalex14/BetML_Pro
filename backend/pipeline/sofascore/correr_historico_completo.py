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
    log.info("Corre hasta que todos los partidos tengan stats")

    ronda = 1
    while True:
        log.info(f"\n{'='*55}")
        log.info(f"  RONDA {ronda}")
        log.info(f"{'='*55}")

        correr_job_historico_sofascore()

        log.info(f"Ronda {ronda} completada — pausa de 60 segundos")
        ronda += 1

        # Pausa entre rondas para no saturar Sofascore
        time.sleep(60)


if __name__ == "__main__":
    main()