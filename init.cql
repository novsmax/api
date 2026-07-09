CREATE KEYSPACE IF NOT EXISTS smart_tracker_training
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

CREATE TABLE IF NOT EXISTS smart_tracker_training.active_training (
    user_id uuid,
    active_training_id uuid,
    type_activ_id int,
    date date,
    time_start timestamp,
    training_time int,
    data_training text,
    kilocalories float,
    PRIMARY KEY (user_id, active_training_id)
);

CREATE TABLE IF NOT EXISTS smart_tracker_training.gps_points (
    active_training_id uuid,
    recorded_at timestamp,
    latitude double,
    longitude double,
    accuracy double,
    altitude double,
    speed double,
    batch_id uuid,
    calories double,
    PRIMARY KEY (active_training_id, recorded_at)
);