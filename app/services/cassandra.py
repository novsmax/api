from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import SimpleStatement
import uuid
import os
import logging

logger = logging.getLogger(__name__)


class CassandraService:
    def __init__(self):
        self.cluster = None
        self.session = None

    def connect(self):
        auth = PlainTextAuthProvider(
            username=os.getenv("CASSANDRA_USER", "smart_tracker"),
            password=os.getenv("CASSANDRA_PASSWORD", "your_password_here")
        )
        self.cluster = Cluster(
            contact_points=[os.getenv("CASSANDRA_HOST", "127.0.0.1")],
            port=int(os.getenv("CASSANDRA_PORT", "9042")),
            auth_provider=auth
        )
        self.session = self.cluster.connect("smart_tracker_training")
        logger.info("Подключение к Cassandra установлено")

    def close(self):
        if self.cluster:
            self.cluster.shutdown()
            logger.info("Подключение к Cassandra закрыто")
    # тренировки
    def start_training(self, user_id: uuid.UUID, active_training_id: uuid.UUID, type_activ_id: int):
        self.session.execute(
        """
            INSERT into active_training(user_id, active_training_id, type_activ_id, date, 
                time_start, training_time, is_pause, data_training, kilocalories)
            VALUES (%s, %s, %s, toDate(now()), toTimestamp(now()), 0, false, %s, 0.0)
        """,
        (user_id, active_training_id, type_activ_id, '{}')
        )

    def get_active_training(self, user_id: uuid.UUID):
        rows = self.session.execute(
            "SELECT * FROM active_training WHERE user_id = %s",
            (user_id,)
        )
        return rows.one() if rows else None

    def delete_training(self, user_id: uuid.UUID, active_training_id: uuid.UUID):
        self.session.execute(
            "DELETE FROM active_training WHERE user_id = %s AND active_training_id = %s",
            (user_id, active_training_id)
        )

    # GPS
    def save_gps_points(self, active_training_id: uuid.UUID, batch_id: uuid.UUID, points: list):
        for point in points:
            self.session.execute(
                """
                INSERT into gps_points(active_training_id, recorded_at, latitude, longitude, 
                    accuracy, altitude, speed, batch_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    active_training_id,
                    point['timestamp'],
                    point['latitude'],
                    point['longitude'],
                    point.get("accuracy"),
                    point.get("altitude"),
                    point.get("speed"),
                    batch_id
                )
            )

cassandra_service = CassandraService()