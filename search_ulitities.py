from aiohttp import ClientSession
import asyncio
from typing import Tuple
from bot_enums import Servers, ServerExtensions, Urls, Keys


class Search:
    """
    Handles different async searches needed for the bot
    """

    @staticmethod
    async def async_search(url: str, identifier=None) -> dict:
        """ Handles Async searching and converting to Json data
        can take an identifier for use with as_completed and other yield type with unknown ordering

        :param url: Url to search
        :param identifier: optional: used to index calls with unknown return order
        :return: Data or if id dict[data, id]
        """
        async with ClientSession() as session:
            async with session.get(url) as search:
                if search.status == 200:
                    json_output = await search.json()
        if identifier is None:
            return json_output
        else:
            return {'output': json_output, 'id': identifier}

    @classmethod
    async def gather(cls, *urls):
        """Returns the completed api calls in an iterable; preserves order

        only to be used when all calls are expected to complete, will hang on a slow call
        """
        tasks = [cls.async_search(i) for i in urls]
        return await asyncio.gather(*tasks)

    @classmethod
    async def get_user_server(cls, username: str) -> Tuple[int, Servers]:
        """ Attempts to find the server from a given **user**


        :param username: Name of user, will attempt match but exact name is always better UwU
        :return: user_id and server
        """
        tasks = [cls.async_search(Urls.PLAYER.value.format(i.value, Keys.WOT.value, username), identifier=i) for i in
                 ServerExtensions.list()]
        for i in asyncio.as_completed(tasks):
            output = await i
            if output['output']['status'] != 'error' and output['output']['meta']['count'] != 0:
                user_id = output["output"]['data'][0]['account_id']
                server = output['id']
                return user_id, server
