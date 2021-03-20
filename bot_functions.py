import aiohttp
from typing import Tuple, List, Union
import asyncio


async def fetch(session, url):
    async with session.get(url) as response:
        json_response = await response.json()
        return json_response
class TankData:
    def __init__(self):
        self.tomato_api_url = "https://tomatobackend.herokuapp.com/api/{}/{}"

        self.tank_info_api_url = "https://api.worldoftanks.{}/wot/encyclopedia/vehicles/?application_id=20e1e0e4254d98635796fc71f2dfe741&fields=name%2Cimages%2Cshort_name%2Ctier"
        self.na_image_and_tank_info, self.eu_image_and_tank_info, self.asia_image_and_tank_info = {}, {}, {}
        self.na_moe_data, self.eu_moe_data, self.asia_moe_data, self.na_mastery_data, self.eu_mastery_data, self.asia_mastery_data = {}, {}, {}, {}, {}, {}
    async def update_vehicles_data(self):
        async with aiohttp.ClientSession() as session:
            tasks = [fetch(session, self.tank_info_api_url.format(i)) for i in ['com','eu','asia']] + [fetch(session, self.tomato_api_url.format(i, j)) for i, j in [('moe','com'),('moe','eu'),('moe','asia'),('mastery','com'),('mastery','eu'),('mastery','asia')]]
            output = await asyncio.gather(*tasks)
            self.na_image_and_tank_info = output[0]
            self.eu_image_and_tank_info = output[1]
            self.asia_image_and_tank_info = output[2]
            self.na_moe_data = output[3]
            self.eu_moe_data = output[4]
            self.asia_moe_data = output[5]
            self.na_mastery_data = output[6]
            self.eu_mastery_data = output[7]
            self.asia_mastery_data = output[8]
            for x in self.na_image_and_tank_info, self.eu_image_and_tank_info, self.asia_image_and_tank_info:
                print(x['status'])
            for x in self.na_moe_data, self.eu_moe_data, self.asia_moe_data, self.na_mastery_data, self.eu_mastery_data, self.asia_mastery_data:
                print(x[0]['id'])


def format_slash_choices(choices_input: Union[list,tuple]) -> List[dict]:
    dicts = []
    for item in choices_input:
        formatted = {'name': item.lower(), 'value': item.lower()}
        dicts.append(formatted)
    return dicts


def get_tank_list(server: str, na_api, eu_api, asia_api) -> Tuple[List, List, List, dict]:
    server_to_data = {'com': na_api, 'eu': eu_api, 'asia': asia_api}
    tank_list = [server_to_data[server]['data'][i]['name'] for i in server_to_data[server]['data'] if
                 server_to_data[server]['data'][i]['tier'] >= 5]
    short_name_list = [server_to_data[server]['data'][i]['short_name'] for i in server_to_data[server]['data'] if
                       server_to_data[server]['data'][i]['tier'] >= 5]
    short_and_long_list = tank_list + short_name_list
    short_name_to_long = {}
    for tank_data_from_server in server_to_data[server]['data']:
        short_name_to_long[server_to_data[server]['data'][tank_data_from_server]['short_name']] = \
            server_to_data[server]['data'][tank_data_from_server]['name']
    return tank_list, short_name_list, short_and_long_list, short_name_to_long


def get_wn8_color(wn8: int) -> int:
    if wn8 < 300:
        return 0x930D0D
    elif wn8 < 450:
        return 0xCD3333
    elif wn8 < 650:
        return 0xCC7A00
    elif wn8 < 900:
        return 0xCCB800
    elif wn8 < 1200:
        return 0x849B24
    elif wn8 < 1600:
        return 0x4D7326
    elif wn8 < 2000:
        return 0x4099BF
    elif wn8 < 2450:
        return 0x3972C6
    elif wn8 < 2900:
        return 0x6844d4
    elif wn8 < 3400:
        return 0x522b99
    elif wn8 < 4000:
        return 0x411d73
    elif wn8 < 4700:
        return 0x310d59
    elif wn8 == "-":
        return 0x808080
    else:
        return 0x24073d


def get_short_hand(position: str) -> str:
    short_positions = {'executive_officer': 'XO',
                       'commander': 'CDR',
                       'personnel_officer': 'PO',
                       'combat_officer': 'CO',
                       'recruitment_officer': 'RO',
                       'intelligence_officer': 'IO',
                       'quartermaster': 'QM',
                       'junior_officer': 'JO',
                       'private': "PVT",
                       'recruit': 'RCT',
                       'reservist': 'RES'
                       }
    return short_positions[position]


async def find_server(username: str, api_url: str, api_key: str) -> Tuple[int, str]:
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url.format('com', api_key, username)) as na_search:
            if na_search.status == 200:
                search_na = await na_search.json()
                if search_na['status'] != "error" and search_na['meta']['count'] != 0:
                    stats_user_id = search_na['data'][0]['account_id']
                    return stats_user_id, 'com'

        async with session.get(api_url.format('eu', api_key, username)) as eu_search:
            if eu_search.status == 200:
                search_eu = await eu_search.json()
                if search_eu['status'] != "error" and search_eu['meta']['count'] != 0:
                    stats_user_id = search_eu['data'][0]['account_id']
                    return stats_user_id, 'eu'

        async with session.get(api_url.format('asia', api_key, username)) as asia_search:
            if asia_search.status == 200:
                search_asia = await asia_search.json()
                if search_asia['status'] != "error" and search_asia['meta']['count'] != 0:
                    stats_user_id = search_asia['data'][0]['account_id']
                    return stats_user_id, 'asia'

