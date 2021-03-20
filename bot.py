import discord as discord
from discord import Embed
from discord.ext import commands
from fuzzywuzzy import process
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils import manage_commands
import requests
import asyncio
from typing import Dict, List
from bot_functions import TankData, get_tank_list, get_wn8_color, get_short_hand, find_server, format_slash_choices
import os
import time
tank_data = TankData()


server_list = ('na', 'eu', 'asia')
timeperiod_list = ('24h', '7days', '30days', '60days', '1000battles')
TOKEN = os.environ.get('TOKEN')
client = commands.Bot(command_prefix='$', activity=discord.Game(name='test'))
client.loop.create_task(tank_data.update_vehicles_data())
slash = SlashCommand(client, sync_commands=True)
WOT_API_KEY = '20e1e0e4254d98635796fc71f2dfe741'


class TankDataFormatter:
    def __init__(self, sent_tank, server="com"):
        server_to_data: Dict[str, List[dict]] = {
            'com': [tank_data.na_image_and_tank_info, tank_data.na_moe_data, tank_data.na_mastery_data],
            'eu': [tank_data.eu_image_and_tank_info, tank_data.eu_moe_data, tank_data.eu_mastery_data],
            'asia': [tank_data.asia_image_and_tank_info, tank_data.asia_moe_data, tank_data.asia_mastery_data]}
        self.tank = sent_tank
        self.server = server
        self.data = server_to_data[self.server]
        for tank_id in self.data[0]['data']:
            if self.data[0]['data'][tank_id]['name'] == self.tank:
                self.tankId = tank_id
                for x in self.data[1]:
                    if str(x['id']) == str(self.tankId):
                        self.markData = x
                        break
                for tank in self.data[2]:
                    if tank['id'] == int(self.tankId):
                        self.masteryData = tank
                        break
                break
        if self.server == 'com':
            self.server_name = 'na'
        else:
            self.server_name = self.server
        self.moeEmbed = Embed(title=f"{self.tank} {self.server_name.upper()}")

    def get_moe_embed(self) -> Embed:
        self.moeEmbed.add_field(name='Marks(Dmg + Track/Spot)',
                                value=f"1 Mark: `{self.markData['65']}`\n2 Mark: `{self.markData['85']}`\n3 Mark: `{self.markData['95']}`\n100% MoE: `{self.markData['100']}`")
        self.moeEmbed.add_field(name='Mastery(XP)',
                                value=f"3rd Class: `{self.masteryData['3rd']}`\n2nd Class: `{self.masteryData['2nd']}`\n1st Class: `{self.masteryData['1st']}`\nMastery: `{self.masteryData['ace']}`")
        url = self.data[0]['data'][self.tankId]['images']['big_icon']
        self.moeEmbed.set_thumbnail(url=url)
        return self.moeEmbed


class PlayerStats:
    def __init__(self, user_id: str, server: str, name: str, wot_api_key: str):
        if server == 'com':
            self.time_out_duration = 8
        else:
            self.time_out_duration = 120
        self.clan_api_url = f'https://api.worldoftanks.{server}/wot/clans/accountinfo/?application_id={wot_api_key}&account_id={user_id}'
        self.wot_api_key = wot_api_key
        self.url_domain = server
        if self.url_domain == 'com':
            self.server = 'NA'
        else:
            self.server = self.url_domain
        self.user_name = name
        tomato_player_api_url = 'https://tomatobackend.herokuapp.com/api/player/{}/{}'
        self.user_id = user_id
        self.user_url = tomato_player_api_url.format(server, user_id)
        self.tomato_api_json = requests.get(self.user_url, timeout=self.time_out_duration).json()
        self.overall_stats = self.tomato_api_json['overallStats']
        self.tank_wn8 = self.overall_stats['tankWN8']
        self.recent_24hr = self.tomato_api_json['recents']['recent24hr']
        self.recent_3days = self.tomato_api_json['recents']['recent3days']
        self.recent_7days = self.tomato_api_json['recents']['recent7days']
        self.recent_30days = self.tomato_api_json['recents']['recent30days']
        self.recent_60days = self.tomato_api_json['recents']['recent60days']
        self.recent_1000 = self.tomato_api_json['recents']['recent1000']
        self.overall_wn8: int = self.overall_stats['overallWN8']
        self.total_battles: int = self.tomato_api_json["overall"]['battles']
        self.total_wins: int = self.tomato_api_json["overall"]['wins']
        self.clan_data = requests.get(self.clan_api_url).json()['data']
        if self.clan_data[str(self.user_id)] is None:
            self.isInClan: bool = False
        else:
            self.isInClan = True
            self.clan_name: str = self.clan_data[str(self.user_id)]['clan']['tag']
            self.clanIconUrl: str = self.clan_data[str(self.user_id)]['clan']['emblems']['x64']['portal']
            self.clanPosition: str = self.clan_data[str(self.user_id)]['role']
            self.shortClanPosition: str = get_short_hand(self.clanPosition)

    def get_default_stats(self) -> Embed:

        dataList = {"overall": self.overall_stats, "24h": self.recent_24hr, "7 days": self.recent_7days,
                    '30 days': self.recent_30days, '60 Days': self.recent_60days, '1000 Battles': self.recent_1000}
        if self.isInClan:
            default_stats_embed = Embed(title=f"{self.user_name.capitalize()}'s Stats",
                                        description="**" + self.shortClanPosition + ' ' + "at" + " " f"[{self.clan_name}]" + "**",
                                        color=get_wn8_color(self.overall_wn8),
                                        url=f'http://tomato.gg/stats/{self.server}/{self.user_name}={self.user_id}')
            default_stats_embed.set_thumbnail(url=self.clanIconUrl)

        else:
            default_stats_embed = Embed(title=f"{self.user_name.capitalize()}'s Stats",
                                        colour=get_wn8_color(self.overall_wn8),
                                        url=f'http://tomato.gg/stats/{self.server}/{self.user_name}={self.user_id}')

        for time_period in list(dataList.keys()):
            values = list(dict(list(dataList[time_period].items())[0:4]).values())
            if time_period == 'overall':

                winrate = int(self.total_wins) / int(self.total_battles)
                winRatePercent = "{:.1%}".format(winrate)
                default_stats_embed.add_field(name=f"**{time_period}**",
                                              value=f'Battles: `{values[0]}`\nWN8: `{values[1]}`\nWinRate: `{winRatePercent}`\nAvgTier: `{str(values[2])[0:3]}`',
                                              inline=True)
            else:
                recentBattles = int(values[0])
                recentsWins = dataList[time_period]['wins']
                if recentBattles != 0:
                    recentWinRate = recentsWins / recentBattles
                    recentWinRatePercent = "{:.1%}".format(recentWinRate)

                else:
                    recentWinRatePercent = '-'
                default_stats_embed.add_field(name=time_period,
                                              value=f'Battles: `{values[0]}`\nWN8: `{values[3]}`\nWinRate: `{recentWinRatePercent}`\nAvgTier: `{str(values[2])[0:3]}`')
        default_stats_embed.set_footer(text='Powered by Tomato.gg',
                                       icon_url='https://www.tomato.gg/static/media/smalllogo.70f212e0.png')

        return default_stats_embed

    def get_timeperiod_stats(self, period: str) -> Embed:
        all_periods_data = {"OVERALL": self.overall_stats, "24H": self.recent_24hr, "7DAYS": self.recent_7days,
                     '30DAYS': self.recent_30days, '60DAYS': self.recent_60days, '1000BATTLES': self.recent_1000}

        period_data = all_periods_data[period.upper()]

        sorted_tank_data = sorted(period_data['tankStats'], key=lambda item: item['battles'], reverse=True)

        top_x_tanks = sorted_tank_data[0:5]
        try:
            tankEmbed = Embed(title=f"{self.user_name.capitalize()}'s Stats",
                              description=f"**Last {period} Stats**",
                              color=get_wn8_color(period_data['overallWN8']),
                              url=f'http://tomato.gg/stats/{self.server}/{self.user_name}={self.user_id}')
        except Exception:
            return Embed(title='Invalid Name')
        values: List = list(dict(list(period_data.items())[0:4]).values())
        recentBattles: int = int(values[0])
        recentsWins = all_periods_data[period.upper()]['wins']
        recentWinRate = recentsWins / recentBattles
        recentWinRatePercent = "{:.1%}".format(recentWinRate)
        tankEmbed.add_field(name='Totals',
                            value=f'Battles: `{values[0]}`\nWN8: `{values[3]}`\nWinRate: `{recentWinRatePercent}`\nAvgTier: `{str(values[2])[0:3]}`')
        for tank in top_x_tanks:
            tankEmbed.add_field(name=tank['name'],
                                value=f"Battles: `{tank['battles']}`\nWinRate: `{tank['winrate']}`\nWN8: `{tank['wn8']}`\nDPG: `{tank['dpg']}`")
        return tankEmbed

    def get_main_ranking(self) -> Embed:
        main_ranking_api_url = "https://tomatobackend.herokuapp.com/api/hofmain/{}/{}".format(self.url_domain,
                                                                                              self.user_id)

        self.ranking_data = requests.get(main_ranking_api_url).json()
        self.ranking_color = get_wn8_color(int(self.ranking_data['top']['wn8']['value']))
        if self.isInClan:
            main_ranking_embed = Embed(
                title=f"{self.user_name.capitalize()}'s Ranking ",
                description=f"**{self.shortClanPosition} at [{self.clan_name.upper()}]**", colour=self.ranking_color,
                url=f'http://tomato.gg/stats/{self.server}/{self.user_name}={self.user_id}?page=hall-of-fame')
            main_ranking_embed.set_thumbnail(url=self.clanIconUrl)
        else:
            main_ranking_embed = Embed(title=f"{self.user_name.capitalize()}'s Ranking ", colour=self.ranking_color,
                                       url=f'http://tomato.gg/stats/{self.server}/{self.user_name}={self.user_id}?page=hall-of-fame')
        for section in self.ranking_data['top']:

            if section not in ['total', 'battles', 'dmg_ratio']:
                main_ranking_embed.add_field(name=f"{section.upper()}",
                                             value=f"Rank: `{self.ranking_data['top'][section]['ranking']}`\n{section}: `{self.ranking_data['top'][section]['value']}`")
            if section == 'dmg_ratio':
                main_ranking_embed.add_field(name=f"DMG RATIO",
                                             value=f"Rank: `{self.ranking_data['top'][section]['ranking']}`\nratio: `{self.ranking_data['top'][section]['value']}`")

        main_ranking_embed.set_footer(text='Powered by Tomato.gg || 60 days | 75 battles min | tier 6+',
                                      icon_url='https://www.tomato.gg/static/media/smalllogo.70f212e0.png')

        return main_ranking_embed


@client.event
async def on_ready():
    print('up')


@slash.slash(name="stats", description='WoT Player Statistics',
             options=[manage_commands.create_option(name='user', description='Players Username', option_type=3,
                                                    required=True),
                      manage_commands.create_option(name='server',
                                                    description='Server To search aganist. Options: na, eu, asia.',
                                                    choices=format_slash_choices(server_list),
                                                    option_type=3, required=False),
                      manage_commands.create_option(name='timeperiod',
                                                    description='Options: 24h, 7days, 30days, 60days, 1000battles.',
                                                    choices=format_slash_choices(timeperiod_list), option_type=3,
                                                    required=False)]
             )
async def _stats(ctx: SlashContext, *args):
    await ctx.respond()
    start = time.time()
    api_url = 'https://api.worldoftanks.{}/wot/account/list/?language=en&application_id={}&search={}'
    sent_servers: List[str] = [i for i in args if i in server_list]
    sent_user_name: str = args[0]
    sent_timeperiod: List[str] = [i for i in args if i in timeperiod_list]
    if sent_servers:
        server: str = sent_servers[0]
        if server == 'na':
            parsed_server: str = 'com'
        else:
            parsed_server = server
        search_for_id_json = requests.get(api_url.format(parsed_server, WOT_API_KEY, sent_user_name)).json()
        if search_for_id_json['status'] == "error" or search_for_id_json['meta']['count'] == 0:
            await ctx.send('Missing api data: Invalid username?')
            return
        else:
            user_id = search_for_id_json['data'][0]['account_id']
    else:
        try:
            user_id, parsed_server = await find_server(sent_user_name, api_url, WOT_API_KEY)

        except Exception:
            await ctx.send('Invalid Username (All servers)')
            return
    user_instance: PlayerStats = PlayerStats(user_id, parsed_server, sent_user_name, WOT_API_KEY)
    if sent_timeperiod:
        timeperiod: str = sent_timeperiod[0]
        await ctx.send(embed=user_instance.get_timeperiod_stats(timeperiod))
        end = time.time()
        print(end-start)
        return
    if not sent_timeperiod:
        default_embed = user_instance.get_default_stats()
        await ctx.send(embed=default_embed)
        end = time.time()
        print(end-start)
        return


@slash.slash(name='marks', description='WoT Tank MoE and Mastery',
             options=[
                 manage_commands.create_option(name='tank', description='Name of Tank', option_type=3, required=True),
                 manage_commands.create_option(name='server', description='Options: na, eu, asia. Defaults to na',
                                               choices=format_slash_choices(server_list), option_type=3,
                                               required=False)]
             )
async def _marks(ctx: SlashContext, tank, server='na'):
    await ctx.respond()
    if tank:
        if server == 'na':
            api_domain_server: str = 'com'
        else:
            api_domain_server = server
        sent_tank_name: str = tank.upper()
        tank_list, short_tank_list, short_and_long_list, short_to_long_dict = get_tank_list(api_domain_server,
                                                                                            tank_data.na_image_and_tank_info,
                                                                                            tank_data.eu_image_and_tank_info,
                                                                                            tank_data.asia_image_and_tank_info)
        tank_guess: List[str, int] = process.extractOne(sent_tank_name, list(short_and_long_list))
        tank_name: str = tank_guess[0]
        if tank_name in short_tank_list:
            tank_name = short_to_long_dict[tank_name]
        try:
            user_tank = TankDataFormatter(tank_name, server=api_domain_server)
        except Exception as e:
            await ctx.send('Invalid Tank Name')
            print(e)
            return
        await ctx.send(embed=user_tank.get_moe_embed())


@slash.slash(name='Ranks', description="WoT Hall of Fame Rankings", options=[
    manage_commands.create_option(name='user', description="Player's Username", option_type=3, required=True),
    manage_commands.create_option(name='server',
                                  description='Server To search against.',
                                  choices=format_slash_choices(server_list),
                                  option_type=3, required=False),
])
async def _ranks(ctx: SlashContext, sent_user_name, sent_server=""):
    await ctx.respond()
    api_url = 'https://api.worldoftanks.{}/wot/account/list/?language=en&application_id={}&search={}'
    if sent_server:

        if sent_server == 'na':
            parsed_server = 'com'
        else:
            parsed_server = sent_server
        search_for_id_json = requests.get(api_url.format(parsed_server, WOT_API_KEY, sent_user_name)).json()
        if search_for_id_json['status'] == "error" or search_for_id_json['meta']['count'] == 0:
            await ctx.send('Missing api data: Invalid username?')
            return
        else:
            user_id = search_for_id_json['data'][0]['account_id']
    else:
        try:
            user_id, parsed_server = await find_server(sent_user_name, api_url, WOT_API_KEY)

        except Exception:
            await ctx.send('Invalid Username (All servers)')
            return
    try:
        user_instance = PlayerStats(user_id, parsed_server, sent_user_name, WOT_API_KEY)
    except requests.exceptions.Timeout:
        await ctx.send('api timeout: invalid user?')
        return
    except Exception:
        await ctx.send('I have no idea what broke')
    await ctx.send(embed=user_instance.get_main_ranking())

client.run(TOKEN)
