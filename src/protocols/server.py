import asyncio
from Telemetry import Telemetry
from MissionLink_Server import MissionLink_Server

async def main():

    # --- Criar servidores ---
    telemetry = Telemetry(
        mode="server",
        host="0.0.0.0",
        port=50001
    )

    mission = MissionLink_Server()

    # Exemplo de callback Telemetry
    async def telemetry_rx(payload, addr):
        print(f"[TELEMETRY] Recebido de {addr}: {payload}")

    telemetry.callback_data = telemetry_rx

    # Exemplo de callback MissionLink
    async def mission_rx(connection_ID, payload):
        print(f"[MISSIONLINK] CID={connection_ID} : {payload}")

    async def mission_req(connection_ID, payload) :
        return bytes([0b0001])

    mission.callback_data = mission_rx
    mission.callback_request = mission_req

    # --- Criar tasks ---
    t1 = asyncio.create_task(telemetry.start_server())
    t2 = asyncio.create_task(mission.start())

    print("[SERVERS] Telemetry e MissionLink iniciados. CTRL+C para parar.")

    try:
        await asyncio.gather(t1, t2)

    except asyncio.CancelledError:
        print("\n[SHUTDOWN] A terminar servidores...")

    finally:
        # Encerrar Telemetry
        try:
            await telemetry.shutdown()
        except:
            pass

        # Encerrar MissionLink
        try:
            await mission.end()
        except:
            pass

        print("[SHUTDOWN] Todos os servidores terminados.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[MAIN] Interrompido pelo utilizador.")
