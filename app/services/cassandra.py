from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import SimpleStatement
import uuid
import os
import logging

logger = logging.getLogger(__name__)


class CassandraService:
    """
    Сервис для работы с Apache Cassandra.
    Управляет подключением и операциями с active_training.
    """

    def __init__(self):
        self.cluster = None
        self.session = None

    def connect(self):
        """Подключение к Cassandra"""
        auth = PlainTextAuthProvider(
            username=os.getenv("CASSANDRA_USER", "smart_tracker"),
            password=os.getenv("CASSANDRA_PASSWORD", "your_password_here")
        )
        self.cluster = Cluster(
            contact_points=[os.getenv("CASSANDRA_HOST", "127.0.0.1")],
            port=int(os.getenv("CASSANDRA_PORT", "  ")),
            auth_provider=auth
        )
        self.session = self.cluster.connect("smart_tracker_training")
        logger.info("Подключение к Cassandra установлено")

    def close(self):
        """Закрытие подключения"""
        if self.cluster:
            self.cluster.shutdown()
            logger.info("Подключение к Cassandra закрыто")

    # ── Операции с активными тренировками ──

    def start_training(self, user_id: int, type_activ_id: int) -> uuid.UUID:
        """Начать новую тренировку. Возвращает active_training_id."""
        training_id = uuid.uuid4()
        self.session.execute(
            """
            INSERT INTO active_training 
                (user_id, active_training_id, type_activ_id, date, 
                 time_start, training_time, is_pause, data_training, kilocalories)
            VALUES (%s, %s, %s, toDate(now()), toTimestamp(now()), 0, false, %s, 0.0)
            """,
            (user_id, training_id, type_activ_id, '{}')
        )
        logger.info(f"Тренировка {training_id} начата для user_id={user_id}")
        return training_id

    def update_training(self, user_id: int, training_id: uuid.UUID,
                        training_time: int = None,
                        is_pause: bool = None,
                        data_training: str = None,
                        kilocalories: float = None):
        """Обновить данные активной тренировки."""
        updates = []
        values = []

        if training_time is not None:
            updates.append("training_time = %s")
            values.append(training_time)
        if is_pause is not None:
            updates.append("is_pause = %s")
            values.append(is_pause)
        if data_training is not None:
            updates.append("data_training = %s")
            values.append(data_training)
        if kilocalories is not None:
            updates.append("kilocalories = %s")
            values.append(kilocalories)

        if not updates:
            return

        values.extend([user_id, training_id])
        query = f"""
            UPDATE active_training 
            SET {', '.join(updates)}
            WHERE user_id = %s AND active_training_id = %s
        """
        self.session.execute(query, values)

    def get_active_training(self, user_id: int):
        """Получить активную тренировку пользователя."""
        rows = self.session.execute(
            "SELECT * FROM active_training WHERE user_id = %s",
            (user_id,)
        )
        return rows.one() if rows else None

    def delete_training(self, user_id: int, training_id: uuid.UUID):
        """Удалить активную тренировку (после переноса в PostgreSQL)."""
        self.session.execute(
            "DELETE FROM active_training WHERE user_id = %s AND active_training_id = %s",
            (user_id, training_id)
        )


# ── Синглтон для использования в FastAPI ──
cassandra_service = CassandraService()