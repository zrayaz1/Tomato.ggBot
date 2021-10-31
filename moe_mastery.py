from __future__ import annotations
from search_ulitities import Search
from bot_enums import ServerExtensions, Servers, Urls, Keys
from typing import Tuple, List, Dict
from discord import Embed


class TankData:
    na_tank = None
    eu_tank = None
    asia_tank = None
    na_moe_data = None
    eu_moe_data = None
    asia_moe_data = None
    na_mastery_data = None
    eu_mastery_data = None
    asia_mastery_data = None

    @classmethod
    async def get_data(cls):
        servers = ServerExtensions.literal_list()
        urls = [Urls.TANK_INFO.value.format(i, Keys.WOT.value) for i in servers] + [
            Urls.TOMATO_TANK.value.format(i, j) for i, j in
            [("moe", k) for k in servers] + [("mastery", k) for k in servers]]
        output = await Search.gather(*urls)
        cls.na_tank = output[0]
        cls.eu_tank = output[1]
        cls.asia_tank = output[2]
        cls.na_moe_data = output[3]
        cls.eu_moe_data = output[4]
        cls.asia_moe_data = output[5]
        cls.na_mastery_data = output[6]
        cls.eu_mastery_data = output[7]
        cls.asia_mastery_data = output[8]
        for x in cls.na_tank, cls.eu_tank, cls.asia_tank:
            if x['status']:
                print("Marks Updated")
                break

    @classmethod
    def get_tank_list(cls, server: Servers) -> Tuple[List, List, Dict]:
        server_to_data = {Servers.NA: cls.na_tank, Servers.EU: cls.eu_tank, Servers.ASIA: cls.asia_tank}
        tank_list = [server_to_data[server]['data'][i]['name'] for i in server_to_data[server]['data'] if
                     server_to_data[server]['data'][i]['tier'] >= 5]
        short_name_list = [server_to_data[server]['data'][i]['short_name'] for i in server_to_data[server]['data'] if
                           server_to_data[server]['data'][i]['tier'] >= 5]
        short_and_long_list = tank_list + short_name_list
        short_name_to_long = {}
        for tank_data_from_server in server_to_data[server]['data']:
            short_name_to_long[server_to_data[server]['data'][tank_data_from_server]['short_name']] = \
                server_to_data[server]['data'][tank_data_from_server]['name']
        return short_name_list, short_and_long_list, short_name_to_long


class TankDataFormatter:
    def __init__(self, sent_tank, server: Servers = Servers.NA):
        server_to_data: Dict[Servers, List[dict]] = {
            Servers.NA: [TankData.na_tank, TankData.na_moe_data, TankData.na_mastery_data],
            Servers.EU: [TankData.eu_tank, TankData.eu_moe_data, TankData.eu_mastery_data],
            Servers.ASIA: [TankData.asia_tank, TankData.asia_moe_data, TankData.asia_mastery_data]}
        self.tank = sent_tank
        self.server = server
        self.server_extension = Servers.get_extension(server)
        self.data = server_to_data[self.server]
        for tank_id in self.data[0]['data']:
            if self.data[0]['data'][tank_id]['name'] != self.tank:
                continue
            self.tankId = tank_id
            for x in self.data[1]:
                if str(x['id']) != str(self.tankId):
                    continue
                self.markData = x
            for tank in self.data[2]:
                if tank['id'] != int(self.tankId):
                    continue
                self.masteryData = tank
        self.moeEmbed = Embed(title=f"{self.tank} {self.server.value.upper()}")

    def get_moe_embed(self) -> Embed:
        self.moeEmbed.add_field(name='Marks(Dmg + Track/Spot)',
                                value=f"1 Mark: `{self.markData['65']}`\n"
                                      f"2 Mark: `{self.markData['85']}`\n"
                                      f"3 Mark: `{self.markData['95']}`\n"
                                      f"100% MoE: `{self.markData['100']}`")
        self.moeEmbed.add_field(name='Mastery(XP)',
                                value=f"3rd Class: `{self.masteryData['3rd']}`\n"
                                      f"2nd Class: `{self.masteryData['2nd']}`\n"
                                      f"1st Class: `{self.masteryData['1st']}`\n"
                                      f"Mastery: `{self.masteryData['ace']}`")
        url = self.data[0]['data'][self.tankId]['images']['big_icon']
        self.moeEmbed.set_thumbnail(url=url)
        return self.moeEmbed
