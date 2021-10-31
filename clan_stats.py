from bot_enums import Servers
from search_ulitities import Search
from typing import Dict, Tuple
from bot_enums import Urls, Keys
from discord import Embed


class ClanStats:
    def __init__(self, passed_clan, passed_server: Servers):
        self.server_name = passed_server
        self.server_extension = Servers.get_extension(self.server_name)
        self.clan_search_url = f"https://api.worldoftanks.{self.server_extension.value}/wot/clans/list/?application_id=20e1e0e4254d98635796fc71f2dfe741&search={passed_clan}"
        self.clan = passed_clan

    async def find_clan(self) -> Dict:
        response = await Search.async_search(self.clan_search_url)
        return response

    @staticmethod
    async def get_clan_data(server, clan_id) -> Tuple:
        clan_data_urls = [Urls.STRONGHOLD, Urls.GLOBAL_MAP, Urls.CLAN_RATING]
        urls = [(i.value.format(server, Keys.WOT.value, clan_id)) for i in clan_data_urls]
        urls.append(Urls.TOMATO_CLAN.value.format(server, clan_id))
        return await Search.gather(*urls)

    async def create_embed(self, clan_id, clan_tag):
        clan_data = await self.get_clan_data(self.server_extension.value, clan_id)
        stronghold, globalmap, clan_rating, tomato_data = clan_data[0], clan_data[1], clan_data[2], clan_data[3]
        clan_name = globalmap['data'][str(clan_id)]['name']
        clan_motto = tomato_data['motto']
        clan_url = tomato_data['emblems']['x64']['portal']
        clan_embed = Embed(title=f'[{self.clan.upper()}] {clan_name}', description=clan_motto)
        global_win_rate = 0
        battles_10 = globalmap['data'][str(clan_id)]['statistics']['battles_10_level']
        if battles_10 != 0:
            global_win_rate = "{:.1%}".format(globalmap['data'][str(clan_id)]['statistics']['wins_10_level'] /
                                              battles_10)
        clan_embed.set_thumbnail(url=clan_url)
        clan_embed.add_field(name='Player Stats', value=f"Overall WN8: `{str(tomato_data['overallWN8'])[0:4]}`\n"
                                                        f"Overall WR: `{str(tomato_data['overallWinrate'])[0:4]}`\n"
                                                        f"Recent WN8: `{str(tomato_data['recentWN8'])[0:4]}`\n"
                                                        f"Recent WR: `{str(tomato_data['recentWinrate'])[0:4]}`")

        # Formatting the general stats to fill page
        clan_embed.add_field(name='General Stats',
                             value=f"Clan Rating: `{str(clan_rating['data'][str(clan_id)]['efficiency']['value'])}`\n"
                                   f"Avg. Daily Battles: `{str(clan_rating['data'][str(clan_id)]['battles_count_avg_daily']['value'])[0:4]}`\n"
                                   f"Avg. PR: `{str(clan_rating['data'][str(clan_id)]['global_rating_weighted_avg']['value'])[0:4]}`\n"
                                   f"Players: `{str(tomato_data['members_count'])[0:2]}`")

        # Formatting Stronghold Stats using clanRating, no idea for what the stronghold endpoint is for
        clan_embed.add_field(name='Stronghold Stats',
                             value=f"SH Tier X ELO: `{str(clan_rating['data'][str(clan_id)]['fb_elo_rating_10']['value'])[0:4]}`\n"
                                   f"SH Tier VIII ELO: `{str(clan_rating['data'][str(clan_id)]['fb_elo_rating_8']['value'])[0:4]}`\n"
                                   f"SH Tier VI ELO: `{str(clan_rating['data'][str(clan_id)]['fb_elo_rating_6']['value'])[0:4]}`",
                             inline=True)

        # Formatting for Global Map ELO uses the ClanRating API endpoint instead of the global map for the ELO
        clan_embed.add_field(name='Global Map Stats',
                             value=f"Global Map ELO: `{str(clan_rating['data'][str(clan_id)]['gm_elo_rating_10']['value'])[0:4]}`\n"
                                   f"Global Map WR: `{str(global_win_rate)[0:5]}`\n"
                                   f"Provinces: `{str(globalmap['data'][str(clan_id)]['statistics']['provinces_count'])[0:4]}`",
                             inline=False)

        # converts string hex to int hex format
        clan_embed.colour = int("0x" + tomato_data['color'][1:], 0)

        # Gamer Footer
        clan_embed.set_footer(text='Powered by Tomato.gg',
                              icon_url='https://www.tomato.gg/static/media/smalllogo.70f212e0.png')

        # Make name a clickable link to clan page
        clan_embed.url = f"https://www.tomato.gg/clan-stats/{self.server_name.value}/{clan_tag}={clan_id}"
        return clan_embed
