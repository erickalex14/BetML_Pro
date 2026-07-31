import logging
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from functools import lru_cache
from backend.core.config import get_settings

log = logging.getLogger(__name__)

class ModeloService:
    """
    Gestiona el ciclo de vida del modelo ML
    """

    def __init__(self):
        self.settings = get_settings()
        self._modelo = None
        self._cargar_modelo()  # ← con guión bajo


    #Cargar el modelo
    def _cargar_modelo(self):
        ruta = Path("data/models") / self.settings.model_name
        if ruta.exists():
            self._modelo = joblib.load(ruta)
            log.info(f"Modelo cargado: {ruta}")
        else:
            log.warning(f"Modelo no encontrado: {ruta}, entrena primero el modelo con el entrenador.py")



    @property
    def disponible(self) -> bool:
        return self._modelo is not None




    #pREDECIR PROBABILIDAD
    def predecir_proba(self, X: pd.DataFrame)-> np.ndarray:
        if not self.disponible:
            raise RuntimeError("Modelo non disponible")
        return self._modelo.predict_proba(X)



    #RECARGAR EL MODELO DESDE EL DISCO, PARA REENTRENAR
    def recargar(self):
        self._modelo = None
        self._cargar_modelo()

@lru_cache()
def get_modelo_service() -> ModeloService:
    return ModeloService()
