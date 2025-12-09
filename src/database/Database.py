import aiosqlite
from typing import Any
import csv
from common.Message import *
from common.Mission import *
from rover.Rover import status_dict


class DatabaseException(Exception):
    pass


class Database:
    def __init__(self, db_path: str = "../files/database.db"):
        self.db_path = db_path

    # -------------------- Initialization --------------------
    async def init(self):
        try:
            self.__connection = await aiosqlite.connect(self.db_path)
            self.__connection.row_factory = aiosqlite.Row

            # TABLE: missions
            await self.__execute_sql('''
                CREATE TABLE IF NOT EXISTS missions (
                    mission_id INTEGER PRIMARY KEY,
                    geographic_area TEXT,
                    task TEXT,
                    max_duration INTEGER,
                    atualization_interval INTEGER,
                    status TEXT
                );
            ''')

            # TABLE: rover
            await self.__execute_sql('''
                CREATE TABLE IF NOT EXISTS rover (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rover_id INTEGER,
                    status TEXT,
                    position TEXT,
                    last_update DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            ''')

            # TABLE: rover_mission
            await self.__execute_sql('''
                CREATE TABLE IF NOT EXISTS rover_mission (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rover_id INTEGER NOT NULL,
                    mission_id INTEGER NOT NULL,
                    mission_status TEXT,
                    current_duration INTEGER,
                    completion INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (rover_id) REFERENCES rover(rover_id),
                    FOREIGN KEY (mission_id) REFERENCES missions(mission_id)
                );
            ''')

        except aiosqlite.Error as e:
            raise DatabaseException() from e

    # -------------------- Private method --------------------
    async def __execute_sql(self, sql: str, data: tuple[Any, ...] = ()) -> aiosqlite.Cursor:
        if self.__connection is None:
            raise DatabaseException("Database not initialized. Call await db.init().")

        try:
            cursor = await self.__connection.execute(sql, data)
            return cursor
        except aiosqlite.Error as e:
            raise DatabaseException() from e
        finally :
            await self.__connection.commit()

    # -------------------- Missions --------------------
    async def insert_mission(self, mission: dict):
        sql = """
            INSERT OR REPLACE INTO missions
            (mission_id, geographic_area, task, max_duration, atualization_interval,status)
            VALUES (?, ?, ?, ?, ?, ?);
        """
        values = (
            mission["mission_id"],
            mission["geographic_area"],
            mission["task"],
            mission["max_duration"],
            mission["atualization_interval"],
            mission_status_dict[0]
        )
        await self.__execute_sql(sql, values)

    async def load_missions_from_csv(self, csv_path: str):
        try:
            with open(csv_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row["mission_id"] = int(row["mission_id"])
                    row["max_duration"] = int(row["max_duration"])
                    row["atualization_interval"] = int(row["atualization_interval"])
                    await self.insert_mission(row)
        except FileNotFoundError:
            raise DatabaseException(f"CSV file not found: {csv_path}")
        except Exception as e:
            raise DatabaseException() from e

    async def get_mission(self) -> Mission | None:
        sql = "SELECT mission_id, geographic_area, task, max_duration, atualization_interval FROM missions WHERE status=? ORDER BY RANDOM() LIMIT 1;"
        cursor = await self.__execute_sql(sql,(mission_status_dict[0],))

        row = await cursor.fetchone()
        if row is None:
            return None

        return Mission(row[0], row[1], row[2], row[3], row[4])

    async def get_missions(self) -> dict:
        sql = "SELECT * FROM missions"
        cursor = await self.__execute_sql(sql)
        rows = await cursor.fetchall()

        if rows is None:
            return [{}]

        return [dict(row) for row in rows]

    async def update_missions(self,mission_id,status):
        sql = "UPDATE missions SET status = ? Where mission_id = ?"
        await self.__execute_sql(sql,(mission_status_dict[status], mission_id))



    # -------------------- Rover --------------------
    async def insert_or_update_rover(self, telemetry: Message_Telemetry):
        sql = """
            INSERT INTO rover (rover_id, status, position, last_update)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """
        await self.__execute_sql(sql, (
            telemetry.rover_id,
            status_dict[telemetry.rover_status],
            str(telemetry.rover_position)
        ))

    async def get_rovers(self) -> dict:
        sql = "SELECT * FROM rover"
        cursor = await self.__execute_sql(sql)
        rows = await cursor.fetchall()

        if rows is None:
            return [{}]

        return [dict(row) for row in rows]

    # -------------------- Rover Mission --------------------
    async def insert_rover_mission(self, result: Message_Status):
        sql = """
            INSERT INTO rover_mission
            (rover_id, mission_id, mission_status, current_duration, completion)
            VALUES (?, ?, ?, ?, ?);
        """
        await self.__execute_sql(sql, (
            result.rover_id,
            result.mission_id,
            status_dict[result.status],
            result.current_duration,
            result.completion
        ))

    async def get_RoversMissions(self):
        sql = "SELECT * FROM rover_mission ORDER BY id DESC LIMIT 5;"
        cursor = await self.__execute_sql(sql)
        rows = await cursor.fetchall()

        if rows is None:
            return [{}]

        return [dict(row) for row in rows]

    async def close(self) :
        await self.__connection._stop_running()