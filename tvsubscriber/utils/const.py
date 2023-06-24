from pathlib import Path
from typing import Literal

from httpx import URL

MLSUB = URL('https://rec.mlsub.net/api/user')


class API:
    LOGIN = URL('/login.php')
    GET_CHANNEL = URL('/get-channel.php')
    GET_EPG = URL('/get-epg.php')
    SUBSCRIBE = URL('/addres.php')
    USERINFO = URL('/userinfo.php')
    GET_ORDER = URL('/get-order.php')


ROOT = Path(__file__).parents[1]

NETWORK_NAMES = {
    'Kanto': '关东广域',
    'Kansai': '近畿（关西）广域',
    'Nagoya': '中京名古屋广域',
    'Hokaido': '北海道',
    'Other': '其他地方频道',
    'BS': 'BS卫星',
    'CS': 'CS110',
    'CS124': 'CS124'
}
NETWORKS = Literal['Kanto', 'Kansai', 'Nagoya', 'Hokaido', 'Other', 'BS', 'CS', 'CS124']
