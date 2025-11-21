from MissionLink_Client import MissionLink_Client
import asyncio

async def main():
    payload = {
        "identificacao": "Robot",
        "x": 2.0,
        "y": 3.0,
        "estado": "Trabalhar"
    }


    tasks = []
    for i in range(10):
          ligacao = MissionLink_Client()
          if i % 2 == 0 :
            task = asyncio.create_task(ligacao.send_message(bytes([0b11111110]))) #valor random da data e do request
          else :
            task = asyncio.create_task(ligacao.send_request(bytes([0b1111111])))
          tasks.append(task)

    await asyncio.gather(*tasks)



if __name__ == "__main__":
    asyncio.run(main())
