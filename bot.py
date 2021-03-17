import discord as discord
import requests
from discord import *
from discord.ext import commands
from fuzzywuzzy import process
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils import manage_commands
import os
na_image_and_tank_info, eu_image_and_tank_info, asia_image_and_tank_info = {}, {}, {}
na_moe_data, eu_moe_data, asia_moe_data = {}, {}, {}
na_mastery_data, eu_mastery_data, asia_mastery_data = {}, {}, {}

TOKEN = os.environ.get('TOKEN')

client = commands.Bot(command_prefix='$')
slash = SlashCommand(client, sync_commands=True)
guild_ids = [719707418833190995]

def format_time_for_slash():
    list_of_time_dicts = []
    for time_period_no_overall in ["24H", "7DAYS", '30DAYS', '60DAYS', '1000BATTLES']:
        time_choices_dict = {'name': time_period_no_overall.lower(), 'value': time_period_no_overall.lower()}
        list_of_time_dicts.append(time_choices_dict)
    return list_of_time_dicts


def format_regions_for_slash():
    list_of_regions_dicts = []
    for region in ['na', 'eu', 'asia']:
        regions_dict = {"name": region.lower(), 'value': region.lower()}
        list_of_regions_dicts.append(regions_dict)
    return list_of_regions_dicts


def update_mark_data():
    global na_moe_data, eu_moe_data, asia_moe_data, na_mastery_data, eu_mastery_data, asia_mastery_data
    na_moe_data = requests.get("https://gunmarks.poliroid.ru/api/com/vehicles/65,85,95,100").json()
    eu_moe_data = requests.get("https://gunmarks.poliroid.ru/api/eu/vehicles/65,85,95,100").json()
    asia_moe_data = requests.get("https://gunmarks.poliroid.ru/api/asia/vehicles/65,85,95,100").json()
    na_mastery_data = requests.get("https://mastery.poliroid.ru/api/com/vehicles").json()
    eu_mastery_data = requests.get("https://mastery.poliroid.ru/api/eu/vehicles").json()
    asia_mastery_data = requests.get("https://mastery.poliroid.ru/api/asia/vehicles").json()


def update_vehicles_data():
    tank_info_api_url = "https://api.worldoftanks.{}/wot/encyclopedia/vehicles/?application_id=20e1e0e4254d98635796fc71f2dfe741&fields=name%2Cimages%2Cshort_name%2Ctier"
    global na_image_and_tank_info, eu_image_and_tank_info, asia_image_and_tank_info
    na_image_and_tank_info = requests.get(tank_info_api_url.format("com")).json()
    eu_image_and_tank_info = requests.get(tank_info_api_url.format('eu')).json()
    asia_image_and_tank_info = requests.get(tank_info_api_url.format('asia')).json()


def get_tank_list(server='com'):
    server_to_data = {'com': na_image_and_tank_info, 'eu': eu_image_and_tank_info, 'asia': asia_image_and_tank_info}
    tank_list = [server_to_data[server]['data'][i]['name'] for i in server_to_data[server]['data'] if
                 server_to_data[server]['data'][i]['tier'] >= 5]
    short_name_list = [server_to_data[server]['data'][i]['short_name'] for i in server_to_data[server]['data'] if
                       server_to_data[server]['data'][i]['tier'] >= 5]

    short_and_long_list = tank_list + short_name_list

    short_to_long_dict = {}
    for tank_data_from_server in server_to_data[server]['data']:
        short_to_long_dict[server_to_data[server]['data'][tank_data_from_server]['short_name']] = \
            server_to_data[server]['data'][tank_data_from_server]['name']
    return tank_list, short_name_list, short_and_long_list, short_to_long_dict


def get_wn8_color(wn8: int):
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


def get_short_hand(position):
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


def find_server(username, api_url, api_key):
    search_na = requests.get(api_url.format('com', api_key, username)).json()

    if search_na['status'] != "error" and search_na['meta']['count'] != 0:
        stats_user_id = search_na['data'][0]['account_id']

        return stats_user_id, 'com'
    else:

        search_eu = requests.get(api_url.format('eu', api_key, username)).json()

        if search_eu['status'] != "error" and search_eu['meta']['count'] != 0:
            stats_user_id = search_eu['data'][0]['account_id']

            return stats_user_id, 'eu'
        else:

            search_asia = requests.get(api_url.format('asia', api_key, username)).json()
            if search_asia['status'] != "error" and search_asia['meta']['count'] != 0:
                stats_user_id = search_asia['data'][0]['account_id']
                return stats_user_id, 'asia'
            else:
                raise Exception


class TankData:
    def __init__(self, sent_tank, server="com"):
        server_to_data = {'com': [na_image_and_tank_info, na_moe_data, na_mastery_data],
                          'eu': [eu_image_and_tank_info, eu_moe_data, eu_mastery_data],
                          'asia': [asia_image_and_tank_info, asia_moe_data, asia_mastery_data]}
        self.tank = sent_tank
        self.server = server
        self.data = server_to_data[self.server]
        for tank_id in self.data[0]['data']:
            if self.data[0]['data'][tank_id]['name'] == self.tank:
                self.tankId = tank_id
                for x in self.data[1]['data']:
                    if str(x['id']) == str(self.tankId):
                        self.markData = x['marks']
                for tank in self.data[2]["data"]:
                    if tank['id'] == int(self.tankId):
                        self.masteryData = tank['mastery']
        if self.server == 'com':
            self.server_name = 'na'
        else:
            self.server_name = self.server
        self.moeEmbed = Embed(title=f"{self.tank} {self.server_name.upper()}")

    def get_moe_embed(self):
        self.moeEmbed.add_field(name='Marks(Dmg + Track/Spot)',
                                value=f"1 Mark: `{self.markData['65']}`\n2 Mark: `{self.markData['85']}`\n3 Mark: `{self.markData['95']}`\n100% MoE: `{self.markData['100']}`")
        self.moeEmbed.add_field(name='Mastery(XP)',
                                value=f"3st Class: `{self.masteryData[0]}`\n2st Class: `{self.masteryData[1]}`\n1st Class: `{self.masteryData[2]}`\nMastery: `{self.masteryData[3]}`")
        url = self.data[0]['data'][self.tankId]['images']['big_icon']
        self.moeEmbed.set_thumbnail(url=url)
        return self.moeEmbed


class PlayerStats:
    def __init__(self, user_id: str, server: str, name: str, wot_api_key: str):

        if server == 'com':
            self.defaultTimeOut = 8
        else:
            self.defaultTimeOut = 120
        self.clanApiUrl = f'https://api.worldoftanks.{server}/wot/clans/accountinfo/?application_id={wot_api_key}&account_id={user_id}'
        self.apiKey = wot_api_key
        self.server = server
        if self.server == 'com':
            self.parsedServer = 'NA'
        else:
            self.parsedServer = self.server
        self.userName = name
        self.sealClubber = False
        api_url = 'https://tomatobackend.herokuapp.com/api/player/{}/{}'
        self.userId = user_id
        self.userUrl = api_url.format(server, user_id)

        self.jsonOutput = requests.get(self.userUrl, timeout=self.defaultTimeOut).json()

        self.overallStats = self.jsonOutput['overallStats']
        self.tankWN8 = self.overallStats['tankWN8']
        self.recent24hr = self.jsonOutput['recents']['recent24hr']
        self.recent3days = self.jsonOutput['recents']['recent3days']
        self.recent7days = self.jsonOutput['recents']['recent7days']
        self.recent30days = self.jsonOutput['recents']['recent30days']
        self.recent60days = self.jsonOutput['recents']['recent60days']
        self.recent1000 = self.jsonOutput['recents']['recent1000']
        self.overallWN8 = self.overallStats['overallWN8']
        self.clanId = ''
        self.overallWN8Color = get_wn8_color(self.overallWN8)
        self.oneMarks = 0
        self.twoMarks = 0
        self.threeMarks = 0
        self.tier10ThreeMarks = 0
        self.tier10TwoMarks = 0
        self.tier10OneMarks = 0
        self.total_battles = self.jsonOutput["overall"]['battles']
        self.total_wins = self.jsonOutput["overall"]['wins']
        for tank in self.tankWN8:
            if tank['moe'] != 0:
                if tank['moe'] == 1:
                    self.oneMarks += 1
                    if tank['tier'] == 10:
                        self.tier10OneMarks += 1
                elif tank['moe'] == 2:
                    self.twoMarks += 1
                    if tank['tier'] == 10:
                        self.tier10TwoMarks += 1
                elif tank['moe'] == 3:
                    self.threeMarks += 1
                    if tank['tier'] == 10:
                        self.tier10ThreeMarks += 1
        self.startTitleStr = f"{self.userName.capitalize()}'s Stats"
        clan_data = requests.get(self.clanApiUrl).json()['data']
        if clan_data[str(self.userId)] is None:
            self.isInClan = False
        else:
            self.isInClan = True
            self.clanName = clan_data[str(self.userId)]['clan']['tag']
            self.clanIconUrl = clan_data[str(self.userId)]['clan']['emblems']['x64']['portal']
            self.clanPosition = clan_data[str(self.userId)]['role']
            self.shortClanPosition = get_short_hand(self.clanPosition)

    def get_marks(self):
        embed = Embed(title=f"{self.userName}'s Marks", color=self.overallWN8Color)
        embed.add_field(name='Total Marks',
                        value=f"3 Marks: `{self.threeMarks}`\n2 Marks: `{self.twoMarks}`\n 1 Marks: `{self.oneMarks}`")
        embed.add_field(name='Tier 10 Marks',
                        value=f"3 Marks: `{self.tier10ThreeMarks}`\n2 Marks: `{self.tier10TwoMarks}`\n 1 Marks: `{self.tier10OneMarks}`")
        return embed

    def get_default_stats(self):

        dataList = {"overall": self.overallStats, "24h": self.recent24hr, "7 days": self.recent7days,
                    '30 days': self.recent30days, '60 Days': self.recent60days, '1000 Battles': self.recent1000}
        self.startTitleStr = f"{self.userName.capitalize()}'s Stats"
        if self.isInClan:
            default_stats_embed = Embed(title=self.startTitleStr,
                              description="**" + self.shortClanPosition + ' ' + "at" + " " f"[{self.clanName}]" + "**",
                              color=self.overallWN8Color,
                              url=f'http://tomato.gg/stats/{self.parsedServer}/{self.userName}={self.userId}')
            default_stats_embed.set_thumbnail(url=self.clanIconUrl)

        else:
            default_stats_embed = Embed(title=self.startTitleStr, colour=self.overallWN8Color,
                              url=f'http://tomato.gg/stats/{self.parsedServer}/{self.userName}={self.userId}')

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

    def get_tank_stats(self, period):
        data_list = {"OVERALL": self.overallStats, "24H": self.recent24hr, "7DAYS": self.recent7days,
                     '30DAYS': self.recent30days, '60DAYS': self.recent60days, '1000BATTLES': self.recent1000}

        data = data_list[period.upper()]

        sorted_tank_data = sorted(data['tankStats'], key=lambda item: item['battles'], reverse=True)

        top_x_tanks = sorted_tank_data[0:5]
        try:
            tankEmbed = Embed(title=self.startTitleStr,
                              description=f"**Last {period} Stats**",
                              color=get_wn8_color(data['overallWN8']),
                              url=f'http://tomato.gg/stats/{self.parsedServer}/{self.userName}={self.userId}')
        except Exception:
            return Embed(title='Invalid Name')
        values = list(dict(list(data_list[period.upper()].items())[0:4]).values())
        recentBattles = int(values[0])
        recentsWins = data_list[period.upper()]['wins']
        recentWinRate = recentsWins / recentBattles
        recentWinRatePercent = "{:.1%}".format(recentWinRate)
        tankEmbed.add_field(name='Totals',
                            value=f'Battles: `{values[0]}`\nWN8: `{values[3]}`\nWinRate: `{recentWinRatePercent}`\nAvgTier: `{str(values[2])[0:3]}`')
        for tank in top_x_tanks:
            tankEmbed.add_field(name=tank['name'],
                                value=f"Battles: `{tank['battles']}`\nWinRate: `{tank['winrate']}`\nWN8: `{tank['wn8']}`\nDPG: `{tank['dpg']}`")
        return tankEmbed

    def get_main_ranking(self):
        main_ranking_api_url = "https://tomatobackend.herokuapp.com/api/hofmain/{}/{}".format(self.server, self.userId)

        self.ranking_data = requests.get(main_ranking_api_url).json()
        self.ranking_color = get_wn8_color(int(self.ranking_data['top']['wn8']['value']))
        if self.isInClan:
            main_ranking_embed = Embed(
                title=f"{self.userName.capitalize()}'s Ranking ",
                description=f"**{self.shortClanPosition} at [{self.clanName.upper()}]**", colour=self.ranking_color,url=f'http://tomato.gg/stats/{self.parsedServer}/{self.userName}={self.userId}?page=hall-of-fame')
            main_ranking_embed.set_thumbnail(url=self.clanIconUrl)
        else:
            main_ranking_embed = Embed(title=f"{self.userName.capitalize()}'s Ranking ", colour=self.ranking_color,url=f'http://tomato.gg/stats/{self.parsedServer}/{self.userName}={self.userId}?page=hall-of-fame')
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

    def get_tanks_ranking(self):
        pass
update_vehicles_data()
update_mark_data()
print('data up to date')
@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name='/stats or /marks'))
    print('up')


@slash.slash(name="stats", description='WoT Player Statistics',
             options=[manage_commands.create_option(name='user', description='Players Username', option_type=3,
                                                    required=True),
                      manage_commands.create_option(name='server',
                                                    description='Server To search aganist. Options: na, eu, asia.',
                                                    choices=format_regions_for_slash(),
                                                    option_type=3, required=False),
                      manage_commands.create_option(name='timeperiod',
                                                    description='Options: 24h, 7days, 30days, 60days, 1000battles.',
                                                    choices=format_time_for_slash(), option_type=3, required=False)]
             )
async def _stats(ctx: SlashContext,*args):
    server_list = ['na','eu','asia']
    timeperiod_list = ['24h', '7days', '30days', '60days', '1000battles']
    await ctx.respond()
    api_key = '20e1e0e4254d98635796fc71f2dfe741'
    api_url = 'https://api.worldoftanks.{}/wot/account/list/?language=en&application_id={}&search={}'
    sent_server = [i for i in args if i in server_list]
    sent_user_name = args[0]
    timeperiod = [i for i in args if i in timeperiod_list]
    if sent_server:
        sent_server = sent_server[0]
        if sent_server == 'na':
            parsed_server = 'com'
        else:
            parsed_server = sent_server
        search_for_id_json = requests.get(api_url.format(parsed_server, api_key, sent_user_name)).json()
        if search_for_id_json['status'] == "error" or search_for_id_json['meta']['count'] == 0:
            await ctx.send('Missing api data: Invalid username?')
            return
        else:
            user_id = search_for_id_json['data'][0]['account_id']

    else:
        try:
            user_id, parsed_server = find_server(sent_user_name, api_url, api_key)

        except Exception:
            await ctx.send('Invalid Username (All servers)')
            return


    try:

        user_instance = PlayerStats(user_id, parsed_server, sent_user_name, api_key)
    except requests.exceptions.Timeout:
        await ctx.send('api timeout: invalid user?')
        return
    except Exception as e:
        await ctx.send('Unknown Interaction')
        print(e)

    if timeperiod:
        timeperiod = timeperiod[0]
        await ctx.send(embed=user_instance.get_tank_stats(timeperiod))
        return
    if user_instance:
        my_embed = user_instance.get_default_stats()

    await ctx.send(embed=my_embed)


@slash.slash(name='marks', description='WoT Tank MoE and Mastery',
             options=[
                 manage_commands.create_option(name='tank', description='Name of Tank', option_type=3, required=True),
                 manage_commands.create_option(name='server', description='Options: na, eu, asia. Defaults to na',
                                               choices=format_regions_for_slash(), option_type=3,
                                               required=False)]
             )
async def _marks(ctx: SlashContext, tank, server='na'):
    await ctx.respond()
    if tank:

        server = server

        if server == 'na':
            user_server = 'com'
        else:
            user_server = server

        name_str = tank.upper()

        tank_list, short_tank_list, short_and_long_list, short_to_long_dict = get_tank_list(user_server)
        tank_guess = process.extractOne(str(name_str), list(short_and_long_list))

        if tank_guess[0] in short_tank_list:
            formatted_tank_guess = short_to_long_dict[tank_guess[0]]
        else:
            formatted_tank_guess = tank_guess[0]
        try:
            user_tank = TankData(formatted_tank_guess, server=user_server)
        except Exception:
            await ctx.send('Invalid Tank Name')
            return
        await ctx.send(embed=user_tank.get_moe_embed())


@slash.slash(name='Ranks', description="WoT Hall of Fame Rankings", options=[
    manage_commands.create_option(name='user', description="Player's Username", option_type=3, required=True),
    manage_commands.create_option(name='server',
                                  description='Server To search against.',
                                  choices=format_regions_for_slash(),
                                  option_type=3, required=False),
])
async def _ranks(ctx: SlashContext, sent_user_name, sent_server=""):
    await ctx.respond()
    api_key = '20e1e0e4254d98635796fc71f2dfe741'
    api_url = 'https://api.worldoftanks.{}/wot/account/list/?language=en&application_id={}&search={}'
    if sent_server:

        if sent_server == 'na':
            parsed_server = 'com'
        else:
            parsed_server = sent_server
        search_for_id_json = requests.get(api_url.format(parsed_server, api_key, sent_user_name)).json()
        if search_for_id_json['status'] == "error" or search_for_id_json['meta']['count'] == 0:
            await ctx.send('Missing api data: Invalid username?')
            return
        else:
            user_id = search_for_id_json['data'][0]['account_id']
    else:
        try:
            user_id, parsed_server = find_server(sent_user_name, api_url, api_key)

        except Exception:
            await ctx.send('Invalid Username (All servers)')
            return

    try:

        user_instance = PlayerStats(user_id, parsed_server, sent_user_name, api_key)
    except requests.exceptions.Timeout:
        await ctx.send('api timeout: invalid user?')
        return
    except Exception:
        await ctx.send('I have no idea what broke')
    await ctx.send(embed=user_instance.get_main_ranking())

@client.command()
async def servers(ctx):
    activeservers = client.guilds
    for guild in activeservers:
        print(guild.name)
@client.command()
async def wotlabs(ctx):
    await ctx.send(embed=Embed(title='Wotlabs Sucks'))

client.run(TOKEN)