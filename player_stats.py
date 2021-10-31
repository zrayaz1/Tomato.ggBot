from discord import Embed
from search_ulitities import Search
from typing import Dict, Union
from bot_enums import Servers, Recents, Urls
from exceptions import MissingData


class PlayerData:
    """
    separates and stores player data albeit poorly
    now theres another copy of the data stored in memory !THAT IS BAD!
    """

    def __init__(self, data):
        self.clan_data = data['clanData']
        self.overall_stats = data['overallStats']
        self.tank_wn8 = self.overall_stats['tankWN8']
        self.name = data['summary']['nickname']
        self.recent_24hr = data['recents']['recent24hr']
        self.recent_3days = data['recents']['recent3days']
        self.recent_7days = data['recents']['recent7days']
        self.recent_30days = data['recents']['recent30days']
        self.recent_60days = data['recents']['recent60days']
        self.recent_1000 = data['recents']['recent1000']
        self.overall_wn8: int = self.overall_stats['overallWN8']
        self.total_battles: int = data["overallStats"]['battles']
        self.total_wins: int = data["summary"]['statistics']['all']['wins']
        if self.clan_data is None:
            self.isInClan = False
        else:
            self.isInClan = True
            self.clan_name: str = self.clan_data['clan']['tag']
            self.clanIconUrl: str = self.clan_data['clan']['emblems']['x64']['portal']
            self.clanPosition: str = self.clan_data['role']
            self.shortClanPosition: str = get_short_position(self.clanPosition)


class PlayerStats:
    def __init__(self, user_id: str, server: Servers, name: str, wot_api_key: str, cached: bool = True):
        self.is_cached = cached
        self.wot_api_key = wot_api_key
        self.server = server
        self.extension = Servers.get_extension(self.server)
        self.user_name = name
        self.user_id = user_id
        self.user_url = Urls.TOMATO_PLAYER.value.format(self.extension.value,
                                                        f"{self.user_id}?cache={str(self.is_cached).lower()}")
        self.player_data = None

    async def set_default_stats(self) -> None:
        """
        Generates all the player data and assigns it to instance variable player_data
        """
        tomato_data = await Search.async_search(self.user_url)
        if tomato_data is not None:
            self.player_data = PlayerData(tomato_data)
        else:
            raise MissingData("Tomato_data is None, not in cache?")

    async def generate_default_embed(self) -> Embed:
        """
        Generates a Discord.Embed object using the data set by the set_default_stats method
        """
        data: Dict[Recents, Dict] = {Recents.OVERALL: self.player_data.overall_stats,
                                     Recents.R24H: self.player_data.recent_24hr,
                                     Recents.R7DAYS: self.player_data.recent_7days,
                                     Recents.R30DAYS: self.player_data.recent_30days,
                                     Recents.R60DAYS: self.player_data.recent_60days,
                                     Recents.R1000BATTLES: self.player_data.recent_1000}

        default_stats_embed = Embed(
            title=f"{self.player_data.name}'s Stats",
            color=get_wn8_color(self.player_data.overall_wn8),
            url=f'http://tomato.gg/stats/{self.server.value}/{self.player_data.name}={self.user_id}')
        if self.player_data.isInClan:
            default_stats_embed.description = "**" + self.player_data.shortClanPosition + ' ' + "at" + " " f"[{self.player_data.clan_name}]" + "**"
            default_stats_embed.set_thumbnail(url=self.player_data.clanIconUrl)
        if self.is_cached:
            default_stats_embed.title = f"{self.player_data.name}'s Stats **CACHED**"

        for time_period in list(data.keys()):
            if time_period == Recents.OVERALL:
                battles = data[time_period]['battles']
                wn8 = data[time_period]["overallWN8"]
                avg_tier = data[time_period]['avgTier']
                if avg_tier != '-' and avg_tier != 0:
                    avg_tier = str(avg_tier)[0:3]

                win_rate = int(self.player_data.total_wins) / int(self.player_data.total_battles)
                win_rate_percent = "{:.1%}".format(win_rate)
                if win_rate == 100:
                    win_rate_percent = 100
                default_stats_embed.add_field(name=f"**{time_period.value}**",
                                              value=f'Battles: `{battles}`\n'
                                                    f'WN8: `{wn8}`\n'
                                                    f'WinRate: `{win_rate_percent}`\n'
                                                    f'AvgTier: `{avg_tier}`',
                                              inline=True)
            else:
                battles = data[time_period]['battles']
                wn8 = data[time_period]["overallWN8"]
                avg_tier = data[time_period]['tier']
                if avg_tier != '-' and avg_tier != 0:
                    avg_tier = str(avg_tier)[0:3]
                if battles == '-':
                    recent_battles = 0
                else:
                    recent_battles = int(float(battles))
                recents_wins = data[time_period]['wins']
                if recent_battles != 0:
                    recent_win_rate = recents_wins / recent_battles
                    recent_win_percent = "{:.1%}".format(recent_win_rate)

                else:
                    recent_win_percent = '-'
                default_stats_embed.add_field(name=time_period.value,
                                              value=f'Battles: `{battles}`\n'
                                                    f'WN8: `{wn8}`\n'
                                                    f'WinRate: `{recent_win_percent}`\n'
                                                    f'AvgTier: `{avg_tier}`')

        default_stats_embed.set_footer(text='Powered by Tomato.gg',
                                       icon_url=Urls.TOMATO_SMALL_LOGO.value)

        return default_stats_embed

    async def get_time_stats(self, period: Recents) -> Embed:
        if period == Recents.OVERALL:
            return await self.generate_default_embed()
        periods_data = {Recents.OVERALL: self.player_data.overall_stats,
                        Recents.R24H: self.player_data.recent_24hr,
                        Recents.R3DAYS: self.player_data.recent_3days,
                        Recents.R7DAYS: self.player_data.recent_7days,
                        Recents.R30DAYS: self.player_data.recent_30days,
                        Recents.R60DAYS: self.player_data.recent_60days,
                        Recents.R1000BATTLES: self.player_data.recent_1000}

        period_data = periods_data[period]
        # sort the tanks by number of battles played
        sorted_tank_data = sorted(period_data['tankStats'], key=lambda item: item['battles'], reverse=True)
        # pull the top amount of tanks so that it fills out
        top_tanks = sorted_tank_data[0:5]

        if self.is_cached:
            tank_embed = Embed(title=f"{self.player_data.name}'s Stats **CACHED**",
                               description=f"**Last {period.value} Stats**",
                               color=get_wn8_color(period_data['overallWN8']),
                               url=f'http://tomato.gg/stats/{self.server.value}/{self.user_name}={self.user_id}')
        else:
            tank_embed = Embed(title=f"{self.player_data.name}'s Stats",
                               description=f"**Last {period.value} Stats**",
                               color=get_wn8_color(period_data['overallWN8']),
                               url=f'http://tomato.gg/stats/{self.server.value}/{self.user_name}={self.user_id}')

        recent_battles: int = int(period_data['battles'])
        if recent_battles == 0:
            return Embed(title="No Battles in Period")
        recents_wins = period_data['wins']
        recent_win_rate = recents_wins / recent_battles
        recent_win_percent = "{:.1%}".format(recent_win_rate)
        tank_embed.add_field(name='Totals',
                             value=f"Battles: `{period_data['battles']}`\nWN8: `{period_data['overallWN8']}`\nWinRate: `{recent_win_percent}`\nAvgTier: `{period_data['tier'][0:3]}`")
        for tank in top_tanks:
            tank_embed.add_field(name=tank['name'],
                                 value=f"Battles: `{tank['battles']}`\nWinRate: `{tank['winrate']}`\nWN8: `{tank['wn8']}`\nDPG: `{tank['dpg']}`")
        return tank_embed


def get_wn8_color(wn8: Union[str, int]) -> int:
    if wn8 == "-":
        return 0x808080
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
    else:
        return 0x24073d


def get_short_position(position: str) -> str:
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