from unittest import IsolatedAsyncioTestCase, main
from .Database import Database
from common.Message import Message_Telemetry, Message_Status
from common.Mission import Mission
from common.Mission import mission_status_dict


class DatabaseTests(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Base de dados temporária em memória
        self.db = Database(":memory:")
        await self.db.init()

        # Inserção inicial de missões
        await self.db.insert_mission({
            "mission_id": 1,
            "geographic_area": "'Sector A'",
            "task": "Mapping",
            "max_duration": 100,
            "atualization_interval": 10
        })

        await self.db.insert_mission({
            "mission_id": 2,
            "geographic_area": "'Sector B'",
            "task": "Sampling",
            "max_duration": 200,
            "atualization_interval": 20
        })

        # Inserção inicial de telemetria dos rovers
        self.telemetry1 = Message_Telemetry(
            rover_id=10,
            rover_status=0,
            rover_position=(5, 7)
        )
        self.telemetry2 = Message_Telemetry(
            rover_id=20,
            rover_status=1,
            rover_position=(15, 3)
        )

        await self.db.insert_or_update_rover(self.telemetry1)
        await self.db.insert_or_update_rover(self.telemetry2)

        # Inserção inicial de rover_mission
        self.result1 = Message_Status(
            rover_id=10,
            mission_id=1,
            max_duration = 100,
            status=0,
            current_duration=50,
        )
        self.result2 = Message_Status(
            rover_id=20,
            mission_id=2,
            max_duration=200,
            status=1,
            current_duration=80,
        )

        await self.db.insert_rover_mission(self.result1)
        await self.db.insert_rover_mission(self.result2)

    async def asyncTearDown(self):
        await self.db.close()

    # -------------------- Tests --------------------

    async def test_get_missions(self):
        missions = await self.db.get_missions()
        mission_ids = sorted([m["mission_id"] for m in missions])
        self.assertEqual(mission_ids, [1, 2])

    async def test_get_random_mission_available(self):
        mission = await self.db.get_mission()
        self.assertTrue(isinstance(mission, Mission))

    async def test_update_mission_status(self):
        await self.db.update_missions(1, 1)
        missions = await self.db.get_missions()
        updated = next(m for m in missions if m["mission_id"] == 1)
        self.assertEqual(updated["status"], mission_status_dict[1])

    async def test_get_rovers(self):
        rovers = await self.db.get_rovers()
        rover_ids = sorted([r["rover_id"] for r in rovers])
        self.assertEqual(rover_ids, [10, 20])

    async def test_get_rover_missions(self):
        rows = await self.db.get_RoversMissions()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["mission_id"], 2)
        self.assertEqual(rows[1]["mission_id"], 1)

    async def test_insert_telemetry(self):
        telemetry = Message_Telemetry(
            rover_id=30,
            rover_status=0,
            rover_position=(0, 0)
        )
        await self.db.insert_or_update_rover(telemetry)

        rovers = await self.db.get_rovers()
        rover_ids = sorted([r["rover_id"] for r in rovers])
        self.assertEqual(rover_ids, [10, 20, 30])

    async def test_insert_rover_mission(self):
        result = Message_Status(
            rover_id=10,
            mission_id=2,
            max_duration=200,
            status=0,
            current_duration=10,
        )
        await self.db.insert_rover_mission(result)

        missions = await self.db.get_RoversMissions()
        self.assertEqual(missions[0]["mission_id"], 2)


if __name__ == '__main__':
    main()
