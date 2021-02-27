import discord as discord
import requests
from discord import *
from discord.ext import commands
from fuzzywuzzy import process
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils import manage_commands

na_image_api, eu_image_api, asia_image_api = {}, {}, {}
na_moe_data, eu_moe_data, asia_moe_data = {}, {}, {}
na_mastery_data, eu_mastery_data, asia_mastery_data = {}, {}, {}
TOKEN = 'Nzk1MTM4MTQ1MTA0MTY2OTEy.X_FAGg.Z99hiYDDt8DPMpWQRN_nr5wFedU'
localTOKEN = 'Nzg2Njk4ODg1MzI2MzA3MzU4.X9KMbg.CAAz-_qetCkJAV6y4C4VjbKTSCA'

client = commands.Bot(command_prefix='$')
slash = SlashCommand(client, sync_commands=True)  # Declares slash commands through the client.


class TankData:
    def __init__(self, sent_tank, server="com"):
        server_to_data = {'com': [na_image_api, na_moe_data, na_mastery_data],
                          'eu': [eu_image_api, eu_moe_data, eu_mastery_data],
                          'asia': [asia_image_api, asia_moe_data, asia_mastery_data]}
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



colorRatingNew = {
    "very_bad": 0x7d1930,
    "bad": 0xf11919,
    "below_average": 0xff8a00,
    "average": 0xe6df27,
    "above_average": 0x77e812,
    "good": 0x459300,
    "very_good": 0x2ae4ff,
    "great": 0x0077ff,
    "unicum": 0xc64cff,
    "super_unicum": 0x7d2ad8
}


class BotError(Exception):
    pass


def get_tank_list(server='com'):
    server_to_data = {'com': na_image_api, 'eu': eu_image_api, 'asia': asia_image_api}
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


def update_mark_data():
    global na_moe_data, eu_moe_data, asia_moe_data, na_mastery_data, eu_mastery_data, asia_mastery_data
    na_moe_data = requests.get("https://gunmarks.poliroid.ru/api/com/vehicles/65,85,95,100").json()
    eu_moe_data = requests.get("https://gunmarks.poliroid.ru/api/eu/vehicles/65,85,95,100").json()
    asia_moe_data = requests.get("https://gunmarks.poliroid.ru/api/asia/vehicles/65,85,95,100").json()
    na_mastery_data = requests.get("https://mastery.poliroid.ru/api/com/vehicles").json()
    eu_mastery_data = requests.get("https://mastery.poliroid.ru/api/eu/vehicles").json()
    asia_mastery_data = requests.get("https://mastery.poliroid.ru/api/asia/vehicles").json()


def update_vehicles_icons():
    global na_image_api, eu_image_api, asia_image_api
    na_image_api = requests.get(
        "https://api.worldoftanks.com/wot/encyclopedia/vehicles/?application_id=20e1e0e4254d98635796fc71f2dfe741&fields=name%2Cimages%2Cshort_name%2Ctier").json()
    eu_image_api = requests.get(
        "https://api.worldoftanks.eu/wot/encyclopedia/vehicles/?application_id=20e1e0e4254d98635796fc71f2dfe741&fields=name%2Cimages%2Cshort_name%2Ctier").json()
    asia_image_api = requests.get(
        "https://api.worldoftanks.asia/wot/encyclopedia/vehicles/?application_id=20e1e0e4254d98635796fc71f2dfe741&fields=name%2Cimages%2Cshort_name%2Ctier").json()


def get_wn8_color(wn8: int):
    if wn8 >= 2900:
        wn8_color = colorRatingNew['super_unicum']
    elif wn8 >= 2450:
        wn8_color = colorRatingNew['unicum']
    elif wn8 >= 2000:
        wn8_color = colorRatingNew['great']
    elif wn8 >= 1600:
        wn8_color = colorRatingNew['very_good']
    elif wn8 >= 1200:
        wn8_color = colorRatingNew['good']
    elif wn8 >= 900:
        wn8_color = colorRatingNew['above_average']
    elif wn8 >= 650:
        wn8_color = colorRatingNew['average']
    elif wn8 >= 450:
        wn8_color = colorRatingNew['below_average']
    elif wn8 >= 300:
        wn8_color = colorRatingNew['bad']
    else:
        wn8_color = colorRatingNew['very_bad']
    return wn8_color


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


class PlayerStats:
    def __init__(self, user_id: str, server: str, name: str, wot_api_key: str):

        if server == 'com':
            self.defaultTimeOut = 8
        else:
            self.defaultTimeOut = 20
        self.clanApiUrl = f'https://api.worldoftanks.{server}/wot/clans/accountinfo/?application_id={wot_api_key}&account_id={user_id}'
        self.apiKey = wot_api_key
        self.server = server
        if self.server == 'com':
            self.parsedServer = 'NA'
        else:
            self.parsedServer = self.server
        self.userName = name
        self.sealClubber = False
        api_url = 'https://tomatobackend.herokuapp.com/api/abcd/{}/{}'
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

            # + ' ' * offset + self.shortClanPosition + ' ' + "at" + " " f"[{self.clanName}]"
            testEmbed = Embed(title=self.startTitleStr,
                              description="**" + self.shortClanPosition + ' ' + "at" + " " f"[{self.clanName}]" + "**",
                              color=self.overallWN8Color,
                              url=f'http://tomato.gg/stats/{self.parsedServer}/{self.userName}={self.userId}')
            testEmbed.set_thumbnail(url=self.clanIconUrl)



        else:
            testEmbed = Embed(title=self.startTitleStr, colour=self.overallWN8Color,
                              url=f'http://tomato.gg/stats/{self.parsedServer}/{self.userName}={self.userId}')

        for time_period in list(dataList.keys()):
            values = list(dict(list(dataList[time_period].items())[0:4]).values())
            if time_period == 'overall':
                self.total_battles = self.jsonOutput["overall"]['battles']
                total_wins = self.jsonOutput["overall"]['wins']
                winrate = int(total_wins) / int(self.total_battles)
                winRatePercent = "{:.1%}".format(winrate)
                testEmbed.add_field(name=f"**{time_period}**",
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
                testEmbed.add_field(name=time_period,
                                    value=f'Battles: `{values[0]}`\nWN8: `{values[3]}`\nWinRate: `{recentWinRatePercent}`\nAvgTier: `{str(values[2])[0:3]}`')
        testEmbed.set_footer(text='Powered by Tomato.gg',
                             icon_url='https://www.tomato.gg/static/media/smalllogo.70f212e0.png')

        return testEmbed

    def get_tank_stats(self, period):
        data_list = {"OVERALL": self.overallStats, "24H": self.recent24hr, "7DAYS": self.recent7days,
                     '30DAYS': self.recent30days, '60DAYS': self.recent60days, '1000BATTLES': self.recent1000}

        data = data_list[period.upper()]

        sorted_tank_data = sorted(data['tankStats'], key=lambda item: item['battles'], reverse=True)

        top_six = sorted_tank_data[0:6]
        try:
            tankEmbed = Embed(title=self.startTitleStr,
                              description=f"**Last {period} Stats**",
                              color=get_wn8_color(data['overallWN8']),
                              url=f'http://tomato.gg/stats/{self.parsedServer}/{self.userName}={self.userId}')
        except Exception:
            return Embed(title='Invalid Name')
        for tank in top_six:
            tankEmbed.add_field(name=tank['name'],
                                value=f"Battles: `{tank['battles']}`\nWinRate: `{tank['winrate']}`\nWN8: `{tank['wn8']}`\nDPG: `{tank['dpg']}`")
        return tankEmbed
    def get_main_ranking(self):
        main_ranking_api_url = "https://tomatobackend.herokuapp.com/api/hofmain/{}/{}".format(self.server,self.userId)


        self.ranking_data = requests.get(main_ranking_api_url).json()
        self.ranking_color = get_wn8_color(int(self.ranking_data['top']['wn8']['value']))
        if self.isInClan:
            main_ranking_embed = Embed(
                title=f"{self.userName.capitalize()}'s Ranking ",
                description=f"**{self.shortClanPosition} at [{self.clanName.upper()}]**",colour=self.ranking_color)
            main_ranking_embed.set_thumbnail(url=self.clanIconUrl)
        else:
            main_ranking_embed = Embed(title=f"{self.userName.capitalize()}'s Ranking ",colour=self.ranking_color)
        for section in self.ranking_data['top']:

            if section not in ['total','battles','dmg_ratio']:
                main_ranking_embed.add_field(name=f"{section.upper()}",value=f"Rank: `{self.ranking_data['top'][section]['ranking']}`\nValue: `{self.ranking_data['top'][section]['value']}`")
            if section == 'dmg_ratio':
                main_ranking_embed.add_field(name=f"DMG RATIO",value=f"Rank: `{self.ranking_data['top'][section]['ranking']}`\nValue: `{self.ranking_data['top'][section]['value']}`")



        main_ranking_embed.set_footer(text='Powered by Tomato.gg || 60 days | 75 battles min | tier 6+',
                             icon_url='https://www.tomato.gg/static/media/smalllogo.70f212e0.png')





        return main_ranking_embed
    def get_tanks_ranking(self):
        pass

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name='/stats or /marks'))

    print('up')


update_vehicles_icons()
update_mark_data()
list_of_time_dicts = []
for time_period_no_overall in ["24H", "7DAYS", '30DAYS', '60DAYS', '1000BATTLES']:
    time_choices_dict = {}
    time_choices_dict['name'] = time_period_no_overall.lower()
    time_choices_dict['value'] = time_period_no_overall.lower()
    list_of_time_dicts.append(time_choices_dict)
print('finished')


@slash.slash(name="stats", description='WoT Player Statistics',
             options=[manage_commands.create_option(name='user', description='Players Username', option_type=3,
                                                    required=True),
                      manage_commands.create_option(name='server',
                                                    description='Server To search aganist. Options: na, eu, asia.',
                                                    choices=[{"name": "na", "value": "na"},
                                                             {"name": "eu", "value": "eu"},
                                                             {"name": "asia", "value": "asia"}],
                                                    option_type=3, required=False),
                      manage_commands.create_option(name='timeperiod',
                                                    description='Options: 24h, 7days, 30days, 60days, 1000battles.',
                                                    choices=list_of_time_dicts, option_type=3, required=False)]
             )
async def _stats(ctx: SlashContext, user, server="", timeperiod=""):
    await ctx.respond()
    api_key = '20e1e0e4254d98635796fc71f2dfe741'
    api_url = 'https://api.worldoftanks.{}/wot/account/list/?language=en&application_id={}&search={}'

    def find_server(username):

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

    if user:
        print(user)
        sent_username = user
        player_sent_server = server
        sent_time_period = timeperiod
        if player_sent_server:
            server_passed = True
            if player_sent_server == 'na':
                user_server = 'com'
            else:
                user_server = player_sent_server
        else:
            server_passed = False

        if server_passed:
            search_for_id_json = requests.get(api_url.format(user_server, api_key, sent_username)).json()
            if search_for_id_json['status'] == "error" or search_for_id_json['meta']['count'] == 0:
                await ctx.send('Missing api data: Try again')
            else:
                user_id = search_for_id_json['data'][0]['account_id']
        else:
            try:
                user_id, user_server = find_server(sent_username)

            except Exception:
                await ctx.send('Invalid Username (All servers)')
                return

        try:

            user_instance = PlayerStats(user_id, user_server, sent_username, api_key)
        except requests.exceptions.Timeout:
            await ctx.send('api timeout: invalid user?')
            return
        except Exception:
            await ctx.send('I have no idea what broke')


        if sent_time_period:
            sent_time_period = sent_time_period
            await ctx.send(embed=user_instance.get_tank_stats(sent_time_period))
            return

        my_embed = user_instance.get_default_stats()

        await ctx.send(embed=my_embed)


@client.command(aliases=["stat", "Stats", 'Stat', 'ZrayWantsToDie'])
async def stats(ctx, *args):
    print('Stats Called by ' + str(ctx.guild) + " " + str(ctx.message.author) + f" Called on {args[0]}")
    api_key = '20e1e0e4254d98635796fc71f2dfe741'
    api_url = 'https://api.worldoftanks.{}/wot/account/list/?language=en&application_id={}&search={}'

    sent_channel = ctx.channel
    server_list = ['na', 'eu', 'asia', 'ru']

    def find_server(username):

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

    if args:
        time_periods = ["OVERALL", "24H", "7DAYS", '30DAYS', '60DAYS', '1000BATTLES']
        name = args[0]
        server = [i for i in args if i in server_list]
        time = [i for i in args if i.upper() in time_periods]
        if server:
            server_passed = True
            if server[0] == 'na':
                user_server = 'com'
            else:
                user_server = server[0]
        else:
            server_passed = False

        if server_passed:
            search_for_id_json = requests.get(api_url.format(user_server, api_key, name)).json()
            if search_for_id_json['status'] == "error" or search_for_id_json['meta']['count'] == 0:
                await ctx.send('invalid Username')
                return
            else:
                user_id = search_for_id_json['data'][0]['account_id']
        else:
            try:
                user_id, user_server = find_server(name)

            except Exception:
                await sent_channel.send('Invalid Username (All servers)')
                return

        try:

            user_instance = PlayerStats(user_id, user_server, name, api_key)
        except requests.exceptions.Timeout:
            await sent_channel.send('api timeout: invalid user?')
            return
        except Exception:
            return

        if any(item.startswith('-') for item in args):
            sentFlags = [i for i in args if i.startswith('-')]
            if '-marks' in sentFlags or '-all' in sentFlags:
                embed = user_instance.get_marks()
                await sent_channel.send(embed=embed)
        if time:
            time = time[0]
            await sent_channel.send(embed=user_instance.get_tank_stats(time))
            return
        if "-all" in args or not any(item.startswith("-") for item in args):
            my_embed = user_instance.get_default_stats()

            await sent_channel.send(embed=my_embed)
    else:

        await sent_channel.send("Usage: $stats [user] -flags")


@slash.slash(name='marks', description='WoT Tank MoE and Mastery',
             options=[
                 manage_commands.create_option(name='tank', description='Name of Tank', option_type=3, required=True),
                 manage_commands.create_option(name='server', description='Options: na, eu, asia. Defaults to na',
                                               choices=[{"name": "na", "value": "na"}, {"name": "eu", "value": "eu"},
                                                        {"name": "asia", "value": "asia"}], option_type=3,
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
        except BotError:
            await ctx.send('Invalid Tank Name')
            return
        await ctx.send(embed=user_tank.get_moe_embed())


@client.command(aliases=['tankstats', 'tanks', 'Tank'])
async def marks(ctx, *args):
    if args:
        server_list = ['na', 'eu', 'asia']
        server = [i for i in args if i in server_list]
        if server:
            if server[0] == 'na':
                user_server = 'com'
            else:
                user_server = server[0]
        else:
            user_server = 'com'
        name_str = ""
        for _arg in args:
            if _arg not in server_list:
                name_str += str(_arg) + " "
        name_str = name_str[:-1]

        tank_list, short_tank_list, short_and_long_list, short_to_long_dict = get_tank_list(user_server)
        tank_guess = process.extractOne(str(name_str), list(short_and_long_list))
        print(process.extract(str(name_str), list(short_and_long_list)))
        print('Marks Called by ' + str(ctx.guild) + " " + str(ctx.message.author) + f" Called on {name_str}")
        if tank_guess[0] in short_tank_list:
            formatted_tank_guess = short_to_long_dict[tank_guess[0]]
        else:
            formatted_tank_guess = tank_guess[0]
        try:
            user_tank = TankData(formatted_tank_guess, server=user_server)
        except BotError:
            await ctx.send('Invalid Tank Name')
            return
        await ctx.send(embed=user_tank.get_moe_embed())
@slash.slash(name='Ranks',description="WoT Hall of Fame Rankings",options=[
    manage_commands.create_option(name='user',description="Player's Username",option_type=3,required=True),
    manage_commands.create_option(name='server',
                                  description='Server To search aganist.',
                                  choices=[{"name": "na", "value": "na"},
                                           {"name": "eu", "value": "eu"},
                                           {"name": "asia", "value": "asia"}],
                                  option_type=3, required=False),
])
async def _ranks(ctx: SlashContext, user, server=""):
    await ctx.respond()
    api_key = '20e1e0e4254d98635796fc71f2dfe741'
    api_url = 'https://api.worldoftanks.{}/wot/account/list/?language=en&application_id={}&search={}'
    def find_server(username):

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
    if user:
        print(user)
        sent_username = user
        player_sent_server = server

        if player_sent_server:
            server_passed = True
            if player_sent_server == 'na':
                user_server = 'com'
            else:
                user_server = player_sent_server
        else:
            server_passed = False

        if server_passed:
            search_for_id_json = requests.get(api_url.format(user_server, api_key, sent_username)).json()
            if search_for_id_json['status'] == "error" or search_for_id_json['meta']['count'] == 0:
                await ctx.send('Missing api data: Try again')
            else:
                user_id = search_for_id_json['data'][0]['account_id']
        else:
            try:
                user_id, user_server = find_server(sent_username)

            except Exception:
                await ctx.send('Invalid Username (All servers)')
                return

        try:

            user_instance = PlayerStats(user_id, user_server, sent_username, api_key)
        except requests.exceptions.Timeout:
            await ctx.send('api timeout: invalid user?')
            return
        except Exception:
            await ctx.send('I have no idea what broke')
        await ctx.send(embed=user_instance.get_main_ranking())


client.run(TOKEN)
