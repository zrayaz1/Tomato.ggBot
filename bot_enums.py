from __future__ import annotations
from enum import Enum
from typing import List, Union


class ExtendedEnum(Enum):

    @classmethod
    def list(cls) -> List[ExtendedEnum]:
        """ Gets the list of Enum members as the **class**

        :return: list of class members
        """
        return list(map(lambda c: c, cls))

    @classmethod
    def literal_list(cls) -> List[Union[str, int]]:
        """ Gets the list of Enum values

        :return: enum value as str or int
        """
        return list(map(lambda c: c.value, cls))

    @classmethod
    def get_class(cls, value) -> ExtendedEnum:
        """ Called on subclasses of ExtendedEnum gets the Enum from its literal value

        :param value: value of the class to be returned
        :return: class representation of value
        """
        if value in cls.literal_list():
            str_to_class = {}
            for server in cls.list():
                str_to_class[server.value] = server
            return str_to_class[value]
        else:
            raise KeyError(value)


class ServerExtensions(ExtendedEnum):
    NA_EXTENSION = 'com'
    EU_EXTENSION = 'eu'
    ASIA_EXTENSION = 'asia'


class Servers(ExtendedEnum):
    NA = 'NA'
    EU = 'EU'
    ASIA = 'ASIA'

    @classmethod
    def get_extension(cls, server) -> ExtendedEnum:
        """Gets the relevant extension for a given server

        :param server: Servers
        :return: Extension for given server
        """
        if server == cls.NA:
            return ServerExtensions.NA_EXTENSION
        for i in ServerExtensions.list():
            if i.value[0:2] == server.value[0:2]:
                return i


class Recents(ExtendedEnum):
    R24H = '24h'
    R3DAYS = '3days'
    R7DAYS = '7days'
    R30DAYS = '30days'
    R60DAYS = '60days'
    R1000BATTLES = '1000battles'
    OVERALL = 'overall'


class Urls(Enum):
    STRONGHOLD = "https://api.worldoftanks.{}/wot/stronghold/claninfo/?application_id={}&clan_id={}"
    GLOBAL_MAP = "https://api.worldoftanks.{}/wot/globalmap/claninfo/?application_id={}&clan_id={}"
    CLAN_RATING = "https://api.worldoftanks.{}/wot/clanratings/clans/?application_id={}&clan_id={}"
    TOMATO_CLAN = "https://tomatobackend.herokuapp.com/api/clan/{}/{}"
    PLAYER = "https://api.worldoftanks.{}/wot/account/list/?language=en&application_id={}&search={}"
    TOMATO_PLAYER = 'https://tomatobackend.herokuapp.com/api/player/{}/{}'
    TOMATO_TANK = "https://tomatobackend.herokuapp.com/api/{}/{}"
    TANK_INFO = "https://api.worldoftanks.{}/wot/encyclopedia/vehicles/?application_id={}&fields=name%2Cimages%2Cshort_name%2Ctier"
    TOMATO_SMALL_LOGO = "https://www.tomato.gg/static/media/smalllogo.70f212e0.png"


class Keys(Enum):
    WOT = '20e1e0e4254d98635796fc71f2dfe741'
    TEST_TOKEN = ""
    TOKEN = ""
