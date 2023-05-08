from pathlib import Path
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

