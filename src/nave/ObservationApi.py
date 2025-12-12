from aiohttp import web
import asyncio
from database.Database import Database

class ObservationApi:
    bd: Database = None
    host = None
    port = None
    @classmethod
    async def init(cls):
        """
        Inicializa o servidor aiohttp e registra as rotas.
        """
        @web.middleware
        async def cors_middleware(request, handler):
            # Handle preflight requests
            if request.method == "OPTIONS":
                response = web.Response()
            else:
                response = await handler(request)

            # Add CORS headers to all responses
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            return response

        app = web.Application(middlewares=[cors_middleware])

        # Rotas
        app.router.add_get("/active_rovers", cls.get_active_rovers)
        app.router.add_get("/missions", cls.get_missions)
        app.router.add_get("/reports", cls.get_reports)

        # Iniciar servidor
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=ObservationApi.host, port=ObservationApi.port)
        print("Servidor rodando em http://"+ObservationApi.host + ":" + str(ObservationApi.port))
        await site.start()

        # Mantém o servidor ativo
        while True:
            await asyncio.sleep(3600)
    # ------------------- Handlers -------------------- #

    @staticmethod
    async def get_active_rovers(request):
        rovers = await ObservationApi.bd.get_rovers()
        return web.json_response(rovers)

    @staticmethod
    async def get_missions(request):
        missions = await ObservationApi.bd.get_missions()
        return web.json_response(missions)

    @staticmethod
    async def get_reports(request):
        reports = await ObservationApi.bd.get_RoversMissions()
        return web.json_response(reports)


# Execução direta
if __name__ == "__main__":
    ObservationApi.bd = Database()
    asyncio.run(ObservationApi.init())
