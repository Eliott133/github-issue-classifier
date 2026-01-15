import logging

from pymongo import MongoClient
from pymongo.errors import OperationFailure

from src.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoDBClient:
    def __init__(self):
        try:
            logger.info(f"Connexion à MongoDB avec URI: {settings.MONGO_URI}")
            self.client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
            self.client.admin.command("ping")
            self.db = self.client[settings.MONGO_DB_NAME]
            logger.info("Connexion MongoDB réussie")
        except OperationFailure:
            logger.error("Erreur d'authentification MongoDB")
            raise
        except Exception as e:
            logger.error(f"Erreur MongoDB inattendue: {e}")
            raise


mongo_client = MongoDBClient()
