from MissionLink_Server import MissionLink_Server
import asyncio

async def main() :

      ligacao = MissionLink_Server()
      await ligacao.start()
if __name__ == "__main__" :
      asyncio.run(main())