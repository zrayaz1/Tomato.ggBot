import discord as discord
from discord import Embed
from discord.ext import commands
from discord_slash.context import ComponentContext
from fuzzywuzzy import process
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils import manage_commands
from discord_slash.utils.manage_components import create_button, create_actionrow, wait_for_component
from discord_slash.model import ButtonStyle
import aiohttp
from typing import Dict, List, Union
from bot_functions import TankData, get_tank_list, get_wn8_color, get_short_hand, find_server, format_slash_choices, get_clan_stats
import os

tank_data = TankData()

server_list = ('na', 'eu', 'asia')
timeperiod_list = ('24h', '7days', '30days', '60days', '1000battles')
TOKEN = os.environ.get('TOKEN')
client = commands.Bot(command_prefix='$', activity=discord.Game(name='/'))
client.loop.create_task(tank_data.update_vehicles_data())
slash = SlashCommand(client, sync_commands=True)
WOT_API_KEY = '20e1e0e4254d98635796fc71f2dfe741'
player_embeds = {} # format message_id:embed
clan_embeds = {} # format message_id: embed
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
    def __init__(self, user_id: str, server: str, name: str, wot_api_key: str, cached='true'):
        tomato_player_api_url = 'https://tomatobackend.herokuapp.com/api/player/{}/{}'
        self.is_cached = cached
        self.wot_api_key = wot_api_key
        self.url_domain = server
        if self.url_domain == 'com':
            self.server = 'NA'
        else:
            self.server = self.url_domain
        self.user_name = name

        self.user_id = user_id
        self.user_url = tomato_player_api_url.format(server, f"{self.user_id}?cache={str(self.is_cached)}")

    async def get_default_stats(self,generate_embed=True) -> Union[Embed, None]:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.user_url) as search:
                if search.status == 200:
                    self.tomato_api_json = await search.json()
                try:
                    self.clan_data = self.tomato_api_json['clanData']
                except Exception:
                    self.isInClan = False
                self.overall_stats = self.tomato_api_json['overallStats']
              
                self.tank_wn8 = self.overall_stats['tankWN8']
                self.recent_24hr = self.tomato_api_json['recents']['recent24hr']
                self.recent_3days = self.tomato_api_json['recents']['recent3days']
                self.recent_7days = self.tomato_api_json['recents']['recent7days']
                self.recent_30days = self.tomato_api_json['recents']['recent30days']
                self.recent_60days = self.tomato_api_json['recents']['recent60days']
                self.recent_1000 = self.tomato_api_json['recents']['recent1000']
                self.overall_wn8: int = self.overall_stats['overallWN8']
                self.total_battles: int = self.tomato_api_json["overallStats"]['battles']
                self.total_wins: int = self.tomato_api_json["summary"]['statistics']['all']['wins']
                if self.clan_data is None:
                    self.isInClan = False
                else:
                    self.isInClan = True
                    self.clan_name: str = self.clan_data['clan']['tag']
                    self.clanIconUrl: str = self.clan_data['clan']['emblems']['x64']['portal']
                    self.clanPosition: str = self.clan_data['role']
                    self.shortClanPosition: str = get_short_hand(self.clanPosition)
                if generate_embed:
                    dataList = {"overall": self.overall_stats, "24h": self.recent_24hr, "7 days": self.recent_7days,
                                '30 days': self.recent_30days, '60 Days': self.recent_60days, '1000 Battles': self.recent_1000}
                    if self.isInClan:
                        if self.is_cached == 'true':

                            default_stats_embed = Embed(title=f"{self.user_name.capitalize()}'s Stats **CACHED**",
                                                        description="**" + self.shortClanPosition + ' ' + "at" + " " f"[{self.clan_name}]" + "**",
                                                        color=get_wn8_color(self.overall_wn8),
                                                        url=f'http://tomato.gg/stats/{self.server}/{self.user_name}={self.user_id}')
                        elif self.is_cached == 'false':
                            default_stats_embed = Embed(
                                title=f"{self.user_name.capitalize()}'s Stats",
                                description="**" + self.shortClanPosition + ' ' + "at" + " " f"[{self.clan_name}]" + "**",
                                color=get_wn8_color(self.overall_wn8),
                                url=f'http://tomato.gg/stats/{self.server}/{self.user_name}={self.user_id}')
                        else:
                            raise Exception
                        default_stats_embed.set_thumbnail(url=self.clanIconUrl)

                    else:
                        if self.is_cached == 'true':

                            default_stats_embed = Embed(title=f"{self.user_name.capitalize()}'s Stats **CACHED**",

                                                        color=get_wn8_color(self.overall_wn8),
                                                        url=f'http://tomato.gg/stats/{self.server}/{self.user_name}={self.user_id}')
                        elif self.is_cached == 'false':
                            default_stats_embed = Embed(
                                title=f"{self.user_name.capitalize()}'s Stats",
                                color=get_wn8_color(self.overall_wn8),
                                url=f'http://tomato.gg/stats/{self.server}/{self.user_name}={self.user_id}')

                    for time_period in list(dataList.keys()):
                        if time_period == 'overall':
                            battles = dataList[time_period]['battles']
                            wn8 = dataList[time_period]["overallWN8"]
                            AvgTier = dataList[time_period]['avgTier']
                            if AvgTier != '-' and AvgTier != 0:
                                AvgTier = str(AvgTier)[0:3]

                            winrate = int(self.total_wins) / int(self.total_battles)
                            winRatePercent = "{:.1%}".format(winrate)
                            default_stats_embed.add_field(name=f"**{time_period}**",
                                                          value=f'Battles: `{battles}`\nWN8: `{wn8}`\nWinRate: `{winRatePercent}`\nAvgTier: `{AvgTier}`',
                                                          inline=True)
                        else:
                            battles = dataList[time_period]['battles']
                            wn8 = dataList[time_period]["overallWN8"]
                            AvgTier = dataList[time_period]['tier']
                            if AvgTier != '-' and AvgTier != 0:
                                AvgTier = str(AvgTier)[0:3]
                            if battles == '-':
                                recentBattles = 0
                            else:
                                recentBattles = int(float(battles))
                            recentsWins = dataList[time_period]['wins']
                            if recentBattles != 0:
                                recentWinRate = recentsWins / recentBattles
                                recentWinRatePercent = "{:.1%}".format(recentWinRate)

                            else:
                                recentWinRatePercent = '-'
                            default_stats_embed.add_field(name=time_period,
                                                          value=f'Battles: `{battles}`\nWN8: `{wn8}`\nWinRate: `{recentWinRatePercent}`\nAvgTier: `{AvgTier}`')
                    default_stats_embed.set_footer(text='Powered by Tomato.gg',
                                                   icon_url='https://www.tomato.gg/static/media/smalllogo.70f212e0.png')
                     

                    return default_stats_embed
                else:
                    return
    async def get_timeperiod_stats(self, period: str) -> Embed:
        all_periods_data = {"OVERALL": self.overall_stats, "24H": self.recent_24hr, "7DAYS": self.recent_7days,
                            '30DAYS': self.recent_30days, '60DAYS': self.recent_60days, '1000BATTLES': self.recent_1000}

        period_data = all_periods_data[period.upper()]
        # sort the tanks by number of battles played
        sorted_tank_data = sorted(period_data['tankStats'], key=lambda item: item['battles'], reverse=True)
        #pull the top ammount of tanks so that it fills out
        top_x_tanks = sorted_tank_data[0:5]
        try:
            if self.is_cached == 'true':
                tankEmbed = Embed(title=f"{self.user_name.capitalize()}'s Stats **CACHED**",
                                  description=f"**Last {period} Stats**",
                                  color=get_wn8_color(period_data['overallWN8']),
                                  url=f'http://tomato.gg/stats/{self.server}/{self.user_name}={self.user_id}')
            elif self.is_cached == 'false':
                tankEmbed = Embed(title=f"{self.user_name.capitalize()}'s Stats",
                                  description=f"**Last {period} Stats**",
                                  color=get_wn8_color(period_data['overallWN8']),
                                  url=f'http://tomato.gg/stats/{self.server}/{self.user_name}={self.user_id}')
            else:
                raise Exception

        except Exception:
            return Embed(title='Invalid Name')
        recentBattles: int = int(period_data['battles'])
        recentsWins = period_data['wins']
        recentWinRate = recentsWins / recentBattles
        recentWinRatePercent = "{:.1%}".format(recentWinRate)
        tankEmbed.add_field(name='Totals',
                            value=f"Battles: `{period_data['battles']}`\nWN8: `{period_data['overallWN8']}`\nWinRate: `{recentWinRatePercent}`\nAvgTier: `{period_data['tier'][0:3]}`")
        for tank in top_x_tanks:
            tankEmbed.add_field(name=tank['name'],
                                value=f"Battles: `{tank['battles']}`\nWinRate: `{tank['winrate']}`\nWN8: `{tank['wn8']}`\nDPG: `{tank['dpg']}`")
        return tankEmbed

    async def get_main_ranking(self) -> Embed:
        main_ranking_api_url = "https://tomatobackend.herokuapp.com/api/hofmain/{}/{}".format(self.url_domain,
                                                                                              self.user_id)
        async with aiohttp.ClientSession() as session:
            async with session.get(main_ranking_api_url) as search:
                self.ranking_data = await search.json()

                self.ranking_color = get_wn8_color(int(self.ranking_data['top']['wn8']['value']))
                if self.isInClan:
                    if self.is_cached == 'false':
                        main_ranking_embed = Embed(
                            title=f"{self.user_name.capitalize()}'s Ranking",
                            description=f"**{self.shortClanPosition} at [{self.clan_name.upper()}]**",
                            colour=self.ranking_color,
                            url=f'http://tomato.gg/stats/{self.server}/{self.user_name}={self.user_id}?page=hall-of-fame')
                        main_ranking_embed.set_thumbnail(url=self.clanIconUrl)
                    elif self.is_cached == 'true':
                        main_ranking_embed = Embed(
                            title=f"{self.user_name.capitalize()}'s Ranking **CACHED**",
                            description=f"**{self.shortClanPosition} at [{self.clan_name.upper()}]**",
                            colour=self.ranking_color,
                            url=f'http://tomato.gg/stats/{self.server}/{self.user_name}={self.user_id}?page=hall-of-fame')
                        main_ranking_embed.set_thumbnail(url=self.clanIconUrl)

                else:
                    if self.is_cached == 'false':
                        main_ranking_embed = Embed(title=f"{self.user_name.capitalize()}'s Ranking",
                                                   colour=self.ranking_color,
                                                   url=f'http://tomato.gg/stats/{self.server}/{self.user_name}={self.user_id}?page=hall-of-fame')
                    elif self.is_cached == 'true':
                        main_ranking_embed = Embed(title=f"{self.user_name.capitalize()}'s Ranking **CACHED**",
                                                   colour=self.ranking_color,
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

class ClanStats:
    def __init__(self,clan,server):
        if server == "na":
            self.server = "com"
        else:
            self.server = server
        self.server_name = server.upper()
        if server == "com":
            self.server_name = "NA"
        self.clan_search_url = f"https://api.worldoftanks.{self.server}/wot/clans/list/?application_id=20e1e0e4254d98635796fc71f2dfe741&search={clan}"
        self.clan = clan
        
   
       
    async def find_clan(self):
          #attempt to search for clan using imputted name
        async with aiohttp.ClientSession() as session:
            async with session.get(self.clan_search_url) as search:
                # 200 is the success code
                if search.status == 200:
                    search_response = await search.json()
                    if search_response['status'] == "ok" and search_response['meta']['count'] > 0:
                        return search_response
                else:
                    raise Exception
    async def create_embed(self,clan_id,clan_tag):
        #returns all the data for the 4 endpoints in a massive ass list  
        clan_data = await get_clan_stats(self.server,clan_id)
        stronghold_data, globalmap_data, clanrating_data, tomato_data = clan_data[0], clan_data[1], clan_data[2], clan_data[3]
        clan_name = globalmap_data['data'][str(clan_id)]['name']
        clan_motto = tomato_data['motto']
        clan_url = tomato_data['emblems']['x64']['portal']
        clan_embed = Embed(title=f'[{self.clan.upper()}] {clan_name}',description=clan_motto)
        #calc global map winrate because wargaming 
        global_winrate =  "{:.1%}".format(globalmap_data['data'][str(clan_id)]['statistics']['wins_10_level'] / globalmap_data['data'][str(clan_id)]['statistics']['battles_10_level'])
        clan_embed.set_thumbnail(url=clan_url)
        clan_embed.add_field(name='Player Stats', value=f"Overall WN8: `{str(tomato_data['overallWN8'])[0:4]}`\n"
                                                        f"Overall WR: `{str(tomato_data['overallWinrate'])[0:4]}`\n"
                                                        f"Recent WN8: `{str(tomato_data['recentWN8'])[0:4]}`\n"
                                                        f"Recent WR: `{str(tomato_data['recentWinrate'])[0:4]}`")

        #Formatting the general stats to fill page                                                
        clan_embed.add_field(name='General Stats', value=f"Clan Rating: `{str(clanrating_data['data'][str(clan_id)]['efficiency']['value'])}`\n"
                                                        f"Avg. Daily Battles: `{str(clanrating_data['data'][str(clan_id)]['battles_count_avg_daily']['value'])[0:4]}`\n"
                                                        f"Avg. PR: `{str(clanrating_data['data'][str(clan_id)]['global_rating_weighted_avg']['value'])[0:4]}`\n"
                                                        f"Players: `{str(tomato_data['members_count'])[0:2]}`")

        #Formatting Stronghold Stats using clanrating, no idea for what the stronghold endpoint is for
        clan_embed.add_field(name='Stronghold Stats', value=f"SH Tier X ELO: `{str(clanrating_data['data'][str(clan_id)]['fb_elo_rating_10']['value'])[0:4]}`\n"
                                                        f"SH Tier VIII ELO: `{str(clanrating_data['data'][str(clan_id)]['fb_elo_rating_8']['value'])[0:4]}`\n"
                                                        f"SH Tier VI ELO: `{str(clanrating_data['data'][str(clan_id)]['fb_elo_rating_6']['value'])[0:4]}`",inline=True)

        #Formatting for Global Map ELO shit, for some reason uses the ClanRating API endpoint instead of the global map for the ELO
        clan_embed.add_field(name='Global Map Stats', value=f"Global Map ELO: `{str(clanrating_data['data'][str(clan_id)]['gm_elo_rating_10']['value'])[0:4]}`\n"
                                                        f"Global Map WR: `{str(global_winrate)[0:5]}`\n"
                                                        f"Provinces: `{str(globalmap_data['data'][str(clan_id)]['statistics']['provinces_count'])[0:4]}`",inline=False)

        #weird hex formatting is weird                                                 
        clan_embed.color = int("0x" + tomato_data['color'][1:],0)
                                                        
        #Gamer Footer
        clan_embed.set_footer(text='Powered by Tomato.gg',
                                                        icon_url='https://www.tomato.gg/static/media/smalllogo.70f212e0.png')

        #Make name a clickable link to clan page 
        clan_embed.url = f"https://www.tomato.gg/clan-stats/{self.server_name}/{clan_tag}={clan_id}"
        return clan_embed
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
async def _stats(ctx: SlashContext,user,server=None,timeperiod=None):
    await ctx.defer()
   
    api_url = 'https://api.worldoftanks.{}/wot/account/list/?language=en&application_id={}&search={}'
    if server:
        if server == 'na':
            parsed_server: str = 'com'
        else:
            parsed_server = server
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url.format(parsed_server, WOT_API_KEY, user)) as search:
                search_for_id_json = await search.json()
        if search_for_id_json['status'] == "error" or search_for_id_json['meta']['count'] == 0:
            await ctx.send('Missing api data: Invalid username?')
            return
        else:
            user_id = search_for_id_json['data'][0]['account_id']
    else:
        try:
            user_id, parsed_server = await find_server(user, api_url, WOT_API_KEY)

        except Exception:
            await ctx.send('Invalid Username (All servers)')
            return
    try:
        user_instance_cached = PlayerStats(f"{user_id}", parsed_server, user, WOT_API_KEY, cached='true')
    except Exception:
        await ctx.send("Invalid Name or Region")
        return

    
    if timeperiod:
        cached_sent = False
        try:
            await user_instance_cached.get_default_stats(generate_embed=False)
            cached_sent = True
        except Exception:
            cached_sent = False
            pass
        if cached_sent:
            message = await ctx.send(embed=await user_instance_cached.get_timeperiod_stats(timeperiod),)
        user_instance: PlayerStats = PlayerStats(f"{user_id}", parsed_server, user, WOT_API_KEY,
                                                 cached='false')
        await user_instance.get_default_stats(generate_embed=False)
        if cached_sent:
            await message.edit(embed=await user_instance.get_timeperiod_stats(timeperiod))
        else:
            await ctx.send(embed=await user_instance.get_timeperiod_stats(timeperiod))
        return
        
    else:
        # quick dirty fix for making sure that even if the player isnt in the cache it still works
        cached_sent = False
        try:
            message = await ctx.send(embed=await user_instance_cached.get_default_stats())
            cached_sent = True
        except Exception:
            cached_sent = False
        user_instance: PlayerStats = PlayerStats(f"{user_id}", parsed_server, user, WOT_API_KEY,
                                                 cached='false')
        fetched_embed = await user_instance.get_default_stats()
        if cached_sent:
            await message.edit(embed=fetched_embed)
        else:
            message = await ctx.send(embed=fetched_embed)

        player_embeds[message.id] = fetched_embed
    
    #button setup formatting is a bit werid but it works
    buttons = [
            create_button(
            style=ButtonStyle.green,
            label="Clan Stats",
            custom_id='clanbutton'),

            create_button(
            style=ButtonStyle.blurple,
            label='Player Stats',
            custom_id='playerbutton')
            ]
    action_row = create_actionrow(*buttons)     
    
    clan_id = user_instance.clan_data['clan']['clan_id']
    clan_tag = user_instance.clan_data['clan']['tag']
    clan_instance = ClanStats(clan_tag,parsed_server)
    clan_embed = await clan_instance.create_embed(clan_id,clan_tag)
    clan_embeds[message.id] = clan_embed
    await message.edit(components=[action_row])
    #wait for button press to occur
    while True:    
        button_ctx: ComponentContext = await wait_for_component(client,components=action_row)
        # send pre-fetched clan embed only if its not already shown and the clan button was clicked
        if button_ctx.component_id == "clanbutton":
            await button_ctx.edit_origin(embed=clan_embeds[button_ctx.origin_message_id])
        elif button_ctx.component_id == "playerbutton":
            await button_ctx.edit_origin(embed=player_embeds[button_ctx.origin_message_id])
@slash.slash(name='marks', description='WoT Tank MoE and Mastery',
             options=[
                 manage_commands.create_option(name='tank', description='Name of Tank', option_type=3, required=True),
                 manage_commands.create_option(name='server', description='Options: na, eu, asia. Defaults to na',
                                               choices=format_slash_choices(server_list), option_type=3,
                                               required=False)]
             )
async def _marks(ctx: SlashContext, tank, server='na'):
    # convert from common name to the extension for api usage
    if server == 'na':
        server_extension: str = 'com'
    # only needs to be used for na becuase asia, ru, and eu all use the same    
    else:
        server_extension = server

    sent_tank_name: str = tank.upper()
    tank_list, short_tank_list, short_and_long_list, short_to_long_dict = get_tank_list(server_extension,
                                                                                        tank_data.na_image_and_tank_info,
                                                                                        tank_data.eu_image_and_tank_info,
                                                                                        tank_data.asia_image_and_tank_info)
    tank_guess: List[str, int] = process.extractOne(sent_tank_name, list(short_and_long_list))
    # extractone produces a list, only need first element
    tank_name: str = tank_guess[0]
    # gather the tank name if the string matching pulls the short name
    if tank_name in short_tank_list:
        tank_name = short_to_long_dict[tank_name]
    try:
        user_tank = TankDataFormatter(tank_name, server=server_extension)
        # send final embed with all elements
        await ctx.send(embed=user_tank.get_moe_embed())
    except Exception as e:
        await ctx.send('Invalid Tank Name')
        return
    


@slash.slash(name='Ranks', description="WoT Hall of Fame Rankings", options=[
    manage_commands.create_option(name='user', description="Player's Username", option_type=3, required=True),
    manage_commands.create_option(name='server',
                                  description='Server To search against.',
                                  choices=format_slash_choices(server_list),
                                  option_type=3, required=False),
])
async def _ranks(ctx: SlashContext, sent_user_name, sent_server=None):
    api_url = 'https://api.worldoftanks.{}/wot/account/list/?language=en&application_id={}&search={}'
    if sent_server:

        if sent_server == 'na':
            parsed_server = 'com'
        else:
            parsed_server = sent_server
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url.format(parsed_server, WOT_API_KEY, sent_user_name)) as search:
                search_for_id_json = await search.json()
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

    cached_user_instance = PlayerStats(user_id, parsed_server, sent_user_name, WOT_API_KEY, 'true')

    await cached_user_instance.get_default_stats(generate_embed=False)
    message = await ctx.send(embed=await cached_user_instance.get_main_ranking())
    user_instance = PlayerStats(user_id, parsed_server, sent_user_name, WOT_API_KEY, 'false')
    await user_instance.get_default_stats()
    await message.edit(embed=await user_instance.get_main_ranking())

@slash.slash(name='ClanStats',description="WoT Clan Statistics",options=[manage_commands.create_option(name='clan',description='Clan Name',option_type=3,required=True),
                                                                         manage_commands.create_option(name='server',description='Server To search against.',
                                  choices=format_slash_choices(server_list),option_type=3, required=True)])
async def _ClanStats(ctx: SlashContext,clan,server):
    #api calls are slower than 3 seconds must defer
    await ctx.defer()
    clan_instance = ClanStats(clan,server)
    search_response = await clan_instance.find_clan()
    clan_id = search_response['data'][0]['clan_id']
    # set tag for url shit
    clan_tag = search_response['data'][0]['tag']
    clan_embed = await clan_instance.create_embed(clan_id,clan_tag)
    await ctx.send(embed=clan_embed)




client.run(TOKEN)
