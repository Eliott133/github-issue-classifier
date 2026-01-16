import logging

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from src.config import settings

logger = logging.getLogger(__name__)


class MongoDBClient:
    _instance = None

    def __new__(cls):
        """Pattern Singleton pour éviter d'ouvrir 50 connexions."""
        if cls._instance is None:
            cls._instance = super(MongoDBClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialisation de la connexion."""
        try:
            self.client = MongoClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=5000,  # Timeout rapide (5s) pour échouer vite
            )
            self.db = self.client[settings.MONGO_DB_NAME]
            logger.info(
                f"Client MongoDB initialisé sur la base : {settings.MONGO_DB_NAME}"
            )
            logger.info(f"Collections existantes : {self.db.list_collection_names()}")
            logger.info(
                f"Utilisateur MongoDB connecté avec succès : {self.client.address}"
            )
        except Exception as e:
            logger.critical(f"Impossible d'initialiser le client MongoDB: {e}")
            raise e

    def is_healthy(self) -> bool:
        """Check si la base répond (Ping)."""
        try:
            self.client.admin.command("ping")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError):
            logger.error("MongoDB est injoignable.")
            return False

    def get_collection(self, collection_name: str) -> Collection:
        """Récupère une collection de manière sûre."""
        return self.db[collection_name]

    def close(self):
        if self.client:
            self.client.close()
            logger.info("Connexion MongoDB fermée.")


# Instance globale
mongo_client = MongoDBClient()
