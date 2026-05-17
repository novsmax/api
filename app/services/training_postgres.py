from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from uuid import UUID
from typing import Optional
from datetime import date as date_type
import json

from app.models.completed_training import CompletedTraining
#from app.models.training_gps_points import TrainingGPSPoints
from app.models.completed_training import CompletedTraining

class TrainingService:

    async def save_complete_training(
        self,
        db: AsyncSession,
        training_id: UUID,
        user_id: UUID,
        type_activ_id: int,
        date,
        time_start,
        time_end,
        kilocalories: Optional[float],
        gps_points: list
    ):

        if not isinstance(date, date_type):
            date = date_type.fromisoformat(str(date))

        total_calories = None
        avg_speed = None
        gps_track_wkt = None

        if gps_points:
            sorted_points = sorted(gps_points, key=lambda p: p.recorded_at)

            calories_list = [p.calories for p in sorted_points if p.calories is not None]
            if calories_list:
                total_calories = sum(calories_list)

            speed_list = [p.speed for p in sorted_points if p.speed is not None]
            if speed_list:
                avg_speed = sum(speed_list) / len(speed_list)
   
            coords = []
            for p in sorted_points:
                alt = p.altitude if p.altitude is not None else 0.0
                coords.append(f"{p.longitude} {p.latitude} {alt}")
            
            if len(coords) >= 2:
                gps_track_wkt = f"LINESTRING({', '.join(coords)})"

        elevation_gain = None
        if gps_points:
            gain = 0.0
            sorted_pts = sorted(gps_points, key=lambda p: p.recorded_at)
            for i in range(1, len(sorted_pts)):
                prev_alt = sorted_pts[i-1].altitude or 0.0
                curr_alt = sorted_pts[i].altitude or 0.0
                diff = curr_alt - prev_alt
                if diff > 0:
                    gain += diff
            elevation_gain = round(gain, 2)

        complete = CompletedTraining(
            training_id = training_id,
            user_id = user_id,
            type_activ_id = type_activ_id,
            date = date,
            time_start = time_start,
            time_end = time_end,
            kilocalories = total_calories,
            avg_speed=avg_speed,
            data_training = None,
            gps_track=text(f"ST_GeomFromText('{gps_track_wkt}', 4326)") if gps_track_wkt else None,
            elevation_gain=elevation_gain
        )

        db.add(complete)
        await db.flush()

        if gps_track_wkt:
            result = await db.execute(
                text("SELECT ST_Length(gps_track::geography) FROM completed_training WHERE training_id = :id"),
                {"id": str(training_id)}
            )
            distance = result.scalar()
            if distance:
                complete.distance_m = float(distance)

        await db.commit()

    async def get_complete_training(self, db: AsyncSession, training_id: UUID):
        result = await db.execute(
            select(CompletedTraining).where(CompletedTraining.training_id == training_id)
        )
        data_complete_training = result.scalar_one_or_none()
        if not data_complete_training:
            return None

        geojson_result = await db.execute(
            text("SELECT ST_AsGeoJSON(gps_track) as gps_geojson FROM completed_training WHERE training_id = :id"),
            {"id": str(training_id)}
        )
        row = geojson_result.fetchone()
        gps_geojson = None
        if row and row.gps_geojson:
            gps_geojson = json.loads(row.gps_geojson)

        data_complete_training.gps_geojson = gps_geojson
        return data_complete_training

training_service = TrainingService()