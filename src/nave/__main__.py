from .Nave import *
from .ObservationApi import *
import asyncio

async def main():
    nave = Nave(host_adress="10.0.3.20",telem_port=50001,mission_port=50000,api_port=8000)
    await nave.bd.init()
    await nave.bd.load_missions_from_csv("../files/missions.csv")
    # --- Criar tasks ---
    t1 = asyncio.create_task(nave.telemetry.start_server())
    t2 = asyncio.create_task(nave.mission.start())
    t3 = asyncio.create_task(ObservationApi.init())


    print("[SERVERS] Telemetry e MissionLink iniciados. CTRL+C para parar.")

    try:
        await asyncio.gather(t1, t2,t3)

    except asyncio.CancelledError:
        print("\n[SHUTDOWN] A terminar servidores...")

    finally:
        # Encerrar Telemetry
        try:
           await nave.shutdown()
        except Exception as e:
            print(e)
        print("[SHUTDOWN] Todos os servidores terminados.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[MAIN] Interrompido pelo utilizador.")
