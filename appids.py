import asyncio
import aiohttp
import logging


# How often to recache (in seconds).
PERIOD = 24 * 60 * 60
# End point to visit to get the list.
ENDPOINT = 'http://api.steampowered.com/ISteamApps/GetAppList/v0002/'


class AppIdCacher:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._appid2name = {}
        self._name2appid = {}
        self._logger = logging.getLogger(type(self).__name__)

        # Sets the coro to run concurrently
        # in the background.
        self._logger.info('Started appid cache service.')
        asyncio.ensure_future(self._recache())

    async def _recache(self):
        while True:
            with await self._lock:
                resp = await aiohttp.request('GET', ENDPOINT)
                if resp.status != 200:
                    self._logger.error(f'Could not recache. {resp.status}: {resp.reason}')
                else:
                    data = await resp.json()
                    self._appid2name = {a['appid']: a['name'] for a in data['applist']['apps']}
                    self._name2appid = {a['name'].lower().strip(): a['appid'] for a in data['applist']['apps']}

                    self._logger.info(f'Cached {len(self._appid2name)} game IDs.')
            await asyncio.sleep(PERIOD)

    async def lookup_id(self, appid: int, default=None) -> str:
        with await self._lock:
            return self._appid2name.get(appid, default)

    async def lookup_name(self, name: str, default=None) -> int:
        name = name.lower().strip()
        with await self._lock:
            return self._name2appid.get(name, default)
