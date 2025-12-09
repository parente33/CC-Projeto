from .Nave import *
import threading

async def main():
    await bd.init()
    await bd.load_missions_from_csv("../files/missions.csv")
    telemetry.callback_data = telemetry_rx
    mission.callback_data = mission_rx
    mission.callback_request = mission_req

    # --- Criar tasks ---
    t1 = asyncio.create_task(telemetry.start_server())
    t2 = asyncio.create_task(mission.start())
    threading.Thread(target=ObservationApi.start_ObservationApi, daemon = True).start()


    print("[SERVERS] Telemetry e MissionLink iniciados. CTRL+C para parar.")

    try:
        await asyncio.gather(t1, t2)

    except asyncio.CancelledError:
        print("\n[SHUTDOWN] A terminar servidores...")

    finally:
        # Encerrar Telemetry
        try:
            await telemetry.shutdown()
            await mission.end()
        except :
            pass
        print("[SHUTDOWN] Todos os servidores terminados.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[MAIN] Interrompido pelo utilizador.")
