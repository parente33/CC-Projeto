import sqlite3
from typing import Any
import csv
from Message import *
from Mission import *
from rover import status_dict

class DatabaseException(Exception):
    pass


class Database:
    def __init__(self, db_path: str = "database.db"):
        try:
            self.__connection = sqlite3.connect(db_path, check_same_thread=False)

            # TABLE: missions
            self.__execute_sql('''
                CREATE TABLE IF NOT EXISTS missions (
                    mission_id INTEGER PRIMARY KEY,
                    geographic_area TEXT,
                    task TEXT,
                    max_duration INTEGER,
                    atualization_interval INTEGER
                );
            ''')

            # TABLE: rover
            self.__execute_sql('''
                CREATE TABLE IF NOT EXISTS rover (
                    rover_id INTEGER PRIMARY KEY,
                    status TEXT,
                    position TEXT,
                    last_update DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            ''')

            # TABLE: rover_mission (N..N + histórico)
            self.__execute_sql('''
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

        except sqlite3.Error as e:
            raise DatabaseException() from e

    # -------------------- Private method --------------------
    def __execute_sql(self, sql: str, data: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        try:
            cursor = self.__connection.cursor()
            return cursor.execute(sql, data)
        except sqlite3.Error as e:
            raise DatabaseException() from e
        finally:
            self.__connection.commit()

    # -------------------- Missions --------------------
    def insert_mission(self, mission: dict):
        sql = """
            INSERT OR REPLACE INTO missions
            (mission_id, geographic_area, task, max_duration, atualization_interval)
            VALUES (?, ?, ?, ?, ?);
        """
        values = (
            mission["mission_id"],
            mission["geographic_area"],
            mission["task"],
            mission["max_duration"],
            mission["atualization_interval"],
        )
        self.__execute_sql(sql, values)

    def load_missions_from_csv(self, csv_path: str):
        try:
            with open(csv_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row["mission_id"] = int(row["mission_id"])
                    row["max_duration"] = int(row["max_duration"])
                    row["atualization_interval"] = int(row["atualization_interval"])
                    self.insert_mission(row)
        except FileNotFoundError:
            raise DatabaseException(f"CSV file not found: {csv_path}")
        except Exception as e:
            raise DatabaseException() from e


    def get_mission(self) -> Mission| None:
        """
        Devolve uma missão aleatória da base de dados.
        Retorna None se não existir nenhuma missão.
        """
        sql = "SELECT mission_id, geographic_area, task, max_duration, atualization_interval FROM missions ORDER BY RANDOM() LIMIT 1;"
        cursor = self.__execute_sql(sql)

        row = cursor.fetchone()
        if row is None:
            return None

        return Mission(row[0],row[1],row[2],row[3],row[4])

    # -------------------- Rover --------------------
    def insert_or_update_rover(self, telemetry: Message_Telemetry):
        sql = """
            INSERT INTO rover (rover_id, status, position, last_update)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(rover_id) DO UPDATE SET
                status=excluded.status,
                position=excluded.position,
                last_update=CURRENT_TIMESTAMP;
        """
        self.__execute_sql(sql, (telemetry.rover_id, status_dict[telemetry.rover_status], str(telemetry.rover_position)))

    # -------------------- Rover Mission --------------------
    def insert_rover_mission(self,result : Message_Status):
        sql = """
            INSERT INTO rover_mission
            (rover_id, mission_id, mission_status, current_duration,completion)
            VALUES (?, ?, ?, ?, ?);
        """
        self.__execute_sql(sql, (result.rover_id, result.mission_id, status_dict[result.status],result.current_duration,result.completion))
