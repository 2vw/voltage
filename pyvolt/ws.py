from asyncio import get_event_loop, sleep
from aiohttp import ClientSession, ClientWebSocketResponse
from typing import Callable, Any, Dict
from json import loads
from .http import HttpHandler

class WebSocketHandler:
    def __init__(self, client: ClientSession, http: HttpHandler, token: str, dispatch: Callable[..., Any], raw_dispatch: Callable[[Dict[Any, Any]], Any]):
        self.loop = get_event_loop()
        self.client = client
        self.http = http
        self.ws: ClientWebSocketResponse = None
        self.token = token
        self.dispatch = dispatch
        self.raw_dispatch = raw_dispatch

    async def authorize(self):
        await self.ws.send_json({"type": "Authenticate", "token": self.token})
    
    async def heartbeat(self):
        while True:
            await self.ws.ping()
            await sleep(15)

    async def connect(self):
        info = await self.http.query_node()
        ws_url = info["ws"]
        self.ws = await self.client.ws_connect(ws_url)
        await self.authorize()
        self.loop.create_task(self.heartbeat())
        async for msg in self.ws:
            payload = loads(msg.data)
            # self.loop.create_task(self.handle_event(payload))
            self.loop.create_task(self.raw_dispatch(payload))

    async def handle_event(self, payload: dict[any, any]):
        event = payload["type"].lower()
        func = getattr(self, f"handle_{event}")
        await func(payload)