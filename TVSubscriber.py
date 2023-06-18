from json import JSONDecodeError
import httpx
from typing import Literal, Optional, Union

from .utils.const import API, MLSUB, NETWORKS
from .utils.errors import ApiException
from .models import Channel, Event, Reservation, UserInfo


# 不同api返回的id数据类型不一样，内部统一以str处理
class TVSubscriber:
    def __init__(self):
        self._client = httpx.Client(
            base_url=MLSUB,
            headers={
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0",
            },
            # proxies={
            #     "all://": "http://localhost:9999",
            # }
        )
        self._username = ''
        self._token = ''
        self.last_json = {}
        self._last_resp = None  # type: Optional[httpx.Response]

    def _parse_json(self, msg=''):
        # assert decoded json and raise ApiException with msg
        try:
            json = self._last_resp.json()
            return json
        except JSONDecodeError as e:
            raise ApiException(msg or e)

    def _raise_for_json_status(self, msg=''):
        # assert json status
        if self.last_json['response_code'] != 200:
            raise ApiException(msg + (self.last_json.get('information') or ''), response_json=self.last_json)
        return self.last_json

    def login(self, username: str, password: str, **kwargs) -> dict:
        """
        用户登陆

        raise `ApiException` on fail

        Parameters
        ----------
        username: str
            用户名
        password: str
            密码

        Returns
        ----------
        dict:
            With following keys:
            response_code	int		响应码
            responsetime	str	响应时间
            onlinetoken		str	在线Token
            role			int		用户权限
            information		str	补充说明

            Example:
            {'response_code': 200,
             'responsetime': '2023-05-08 15:03:38',
             'onlinetoken': 'xxxxxxxxxxxxxxxxxxxxxxxxxx',
             'role': '1',
             'information': '已成功登陆用户：xxxx'}

        """
        self._last_resp = self._client.post(API.LOGIN,
                                            data={
                                                'username': username,
                                                'password': password,
                                            },
                                            **kwargs)
        # assert status_code
        self._last_resp.raise_for_status()
        self.last_json = self._parse_json()
        # on fail:
        # {'response_code': 403,
        #  'responsetime': '2023-05-08 15:05:09',
        #  'information': '登陆失败，请重试！您当前已尝试：1次'}
        self._raise_for_json_status('登陆失败')
        self._username = username
        self._token = self.last_json['onlinetoken']
        return self.last_json

    def get_channels(self, network: NETWORKS, **kwargs) -> list[Channel]:
        """
        获取频道列表，名称与取值对应关系见`NETWORK_NAMES`

        raise `ApiException` on fail

        Parameters
        ----------
        network: str
            频道所属网络，具体取值详见`NETWORKS`

        Returns
        ----------
        list[Channel]: 频道列表，详见`models.Channel`

        Json response example:
        response_code			int		响应码
        responsetime			str	响应时间
        network					str	频道所属网络，具体取值详见`NETWORKS`
        channels[]				array	频道列表
          -service				str	频道名称
          -sid					int		频道SID
          -tsid（仅BS，CS返回此值）int	频道TSID
          -epgtoken				str	请求EPG需要的token
        {'response_code': 200,
         'responsetime': '2023-05-08 15:39:00',
         'network': 'Kanto',
         'channels': [
            {'service': '011 ＮＨＫ総合１・東京',
             'sid': 1024,
             'epgtoken': '2ff302f0b3a128806025977360a9d504'
            },
            {'service': '081 フジテレビ',
             'sid': 1056,
             'epgtoken': '8ce266805e6b9d8a3248f0d3d144d773'
            },...
          ]}
        """
        self._last_resp = self._client.post(API.GET_CHANNEL,
                                            data={
                                                'token': self._token,
                                                'network': network
                                            },
                                            **kwargs)
        # assert status_code
        self._last_resp.raise_for_status()
        # .json() is None if failed
        self.last_json = self._parse_json('网络名错误')
        self._raise_for_json_status('获取频道列表失败！')
        if 'channels' not in self.last_json:
            raise ApiException('频道列表响应信息格式错误！', response_json=self.last_json)
        try:
            channels = [Channel(**channel, network=network) for channel in self.last_json['channels']]
        except Exception as e:
            raise ApiException('频道列表响应信息格式错误！' + str(e), response_json=self.last_json)

        return channels

    def get_epgs(self, sid: Union[int, str], network: NETWORKS, epgtoken, tsid: Union[int, str] = None, **kwargs) -> list[Event]:
        """
        获取EPG，即指定频道的具体节目表

        raise `ApiException` on fail

        Parameters
        ----
        sid:
            频道SID
        tsid:
            频道TSID
        network:
            频道所属网络
        epgtoken:
            请求EPG需要的token

        Returns
        ----
        list[Event]: 对应频道的节目列表，详见`models.Event`

        Json response example:
        response_code	int		响应码
        responsetime	str	响应时间
        service			str	频道名称
        mins30price		float	频道半小时单价
        count			str		EPG数量
        events[]		array	EPG信息
          -sid			str		频道SID
          -tsid			str		频道TSID
          -onid			str		频道ONID
          -eid			str		节目EID
          -service		str	频道名称
          -startdate	str	节目播出日期
          -starttime	str	节目开始时间
          -timestamp	int		节目开始时间戳
          -week			str		星期（0-6）
          -week_text	str	曜日（日月火水木金土）
          -duration		int		时长（分钟）
          -event_name	str	节目名称
          -event_text	str	节目说明
          -event_ext_text	str	节目补充说明
          -category		str	节目分类（英语）
          -resolution	str	播出分辨率（1080i，480i）
          -network		str	频道所属网络（Kanto，Kansai，Nagoya，BS，CS）
          -price		int|float	价格
          -reservetoken	str	预约需要的token

        {'response_code': 200,
         'responsetime': '2023-05-08 16:16:46',
         'service': 'ＮＨＫ総合１・東京',
         'mins30price': '3.5',
         'count': '460',
         'events': [{
             'sid': '1056',
             'tsid': '32740',
             'onid': '32740',
             'eid': '27472',
             'service': 'フジテレビ',
             'startdate': '2023/05/14',
             'starttime': '23:15:00',
             'timestamp': 1684077300,
             'week': '0',
             'week_text': '日',
             'duration': 30,
             'event_name': 'テレビアニメ「鬼滅の刃」刀鍛冶の里編[字][解][デ]',
             'event_text': '第六話『柱になるんじゃないのか！』',
             'event_ext_text': 'ご案内\n【公式ＨＰ】\nhttps://www.fujitv.co.jp/kimetsu\n番組内容\n＜前回のあらすじ＞\n４体に分裂した半天狗の猛攻に苦戦する炭治郎たち。しかし、禰豆子の血の力により燃えて赤くなった刀を振るい、炭治郎は３体の頸（くび）を同時に斬ることに成功する。玄弥が残りもう一体の鬼の頸を斬っていたことに気づく炭治郎だったが、鬼の頸を持つ玄弥は姿が変わっており……。\n\n第六話『柱になるんじゃないのか！』は５月１４日（日）２３時１５分放送！\n番組内容２\n遊郭での任務を終えた炭治郎たちの次なる物語を描く「刀鍛冶の里編」。炭治郎が向かう先は、刀鍛冶の里。鬼殺隊最強の剣士≪柱≫である、霞柱・時透無一郎と恋柱・甘露寺蜜璃との再会、忍びよる鬼の影。炭治郎たちの新たな戦いが始まる。\n出演者\n竈門炭治郎（かまど・たんじろう）：\u3000花江夏樹\u3000\n竈門禰豆子（かまど・ねずこ）※：\u3000鬼頭明里\u3000\n時透無一郎（ときとう・むいちろう）：\u3000河西健吾\u3000\n甘露寺蜜璃（かんろじ・みつり）：\u3000花澤香菜\u3000\n不死川玄弥（しなずがわ・げんや）：\u3000岡本信彦\u3000\n\n半天狗（はんてんぐ）：\u3000古川登志夫\u3000\n玉壺（ぎょっこ）：\u3000鳥海浩輔\u3000\n\n※禰豆子の「禰」は「ネ＋爾」が正しい表記。\nスタッフ\n【主題歌】\n＜オープニングテーマ＞\nＭＡＮ\u3000ＷＩＴＨ\u3000Ａ\u3000ＭＩＳＳＩＯＮ×ｍｉｌｅｔ\u3000『絆ノ奇跡』\u3000\n＜エンディングテーマ＞\nｍｉｌｅｔ×ＭＡＮ\u3000ＷＩＴＨ\u3000Ａ\u3000ＭＩＳＳＩＯＮ\u3000『コイコガレ』\u3000\n\n【原作】\n吾峠呼世晴（集英社ジャンプ\u3000コミックス刊）\u3000\n【監督】\n外崎春雄\u3000\n【キャラクターデザイン・総作画監督】\n松島晃\u3000\n【脚本制作】\nｕｆｏｔａｂｌｅ\nスタッフ２\n【サブキャラクターデザイン】\n佐藤美幸、梶山庸子、菊池美花\u3000\n【プロップデザイン】\n小山将治\u3000\n【美術監督】\n衛藤功二\u3000\n【撮影監督】\n寺尾優一\u3000\n【３Ｄ監督】\n西脇一樹\u3000\n【色彩設計】\n大前祐子\u3000\n【編集】\n神野学\u3000\n【音楽】\n梶浦由記、椎名豪\u3000\n【アニメーション制作】\nｕｆｏｔａｂｌｅ\u3000\n【製作】\nアニプレックス、集英社、ｕｆｏｔａｂｌｅ\n',
             'category': 'anime',
             'resolution': '1080i',
             'network': 'Kanto',
             'price': 3.5,
             'reservetoken': 'f9baeab748ee25d6420521c4f7b0242c'
             }, ...]
         }
        """
        data = {
            'token': self._token,
            'sid': sid,
            'network': network,
            'epgtoken': epgtoken
        }
        if tsid:
            data['tsid'] = tsid
        self._last_resp = self._client.post(API.GET_EPG, data=data, **kwargs)
        # assert status_code
        self._last_resp.raise_for_status()
        self.last_json = self._parse_json()
        # on fail:
        # {'response_code': 403, 'responsetime': '2023-05-08 17:08:46', 'information': 'EPG Token错误'}
        # note: egptoken可能会随时间改变
        # empty events:
        # {'response_code': 200,
        #  'responsetime': '2023-06-18 15:37:02',
        #  'service': None,
        #  'mins30price': '3.5',
        #  'count': None,
        #  'events': []}
        self._raise_for_json_status('获取EPG信息失败！')
        if 'events' not in self.last_json:
            raise ApiException('节目响应信息格式错误！', response_json=self.last_json)
        try:
            events = [Event(**event) for event in self.last_json['events']
                      if event.get('event_name') and event.get('event_text') and event.get('category')]
        except Exception as e:
            # bad event:
            # { 'sid': '17408',
            #  'tsid': '32480',
            #  'onid': '32480',
            #  'eid': '59722',
            #  'service': 'ＮＨＫ総合１・仙台',
            #  'startdate': '2023/06/19',
            #  'starttime': '01:25:00',
            #  'timestamp': 1687109100,
            #  'week': '1',
            #  'week_text': '月',
            #  'duration': 155,
            #  'event_name': '放送休止', | None
            #  'event_text': '节目无说明信息',
            #  'event_ext_text': '节目无补充信息',
            #  'category': None,
            #  'resolution': '1080i',
            #  'network': 'Other',
            #  'price': 120,
            #  'reservetoken': '1c293c701da634da2b5f1ae3b64ef931'}
            raise ApiException('节目响应信息格式错误！' + str(e), response_json=self.last_json)

        return events

    def subscribe(self, sid: Union[int, str], eid: Union[int, str], tsid: Union[int, str], onid: Union[int, str],
                  price: Union[int, float], network: str, reservetoken: str, **kwargs) -> Reservation:
        """
        预约节目

        raise `ApiException` on fail

        Parameters
        ----
        sid:
            频道SID
        eid:
            节目EID
        tsid:
            频道TSID
        onid:
            频道ONID
        price:
            价格
        network:
            频道所属网络
        reservetoken:
            预约需要的token

        Returns
        ---
        list[Reservation]: 预约结果，详见`models.Reservation`

        Json response example:
        response_code	int	响应码
        responsetime	str	响应时间
        username		str	用户名
        wallet_before	float	预约前余额
        wallet_after	float	预约后余额
        information		str	补充说明
        reservation	    dict	预约信息
          -sid			str	频道SID
          -eid			str	节目EID
          -service		str	频道名称
          -starttime	str	节目开始时间
          -duration		str	时长（分钟）
          -price		str	价格（若为整数则不能带小数点）
          -resid		str	预约ID
          -orderid		str	订单ID
          -server		int	已预约服务器编号和
                            0：数据库已记录
                            -1：无效
                            以0为基准#REC 01预约则将值+1
                            #REC 02则+2 #REC BACKUP则+4

        {'response_code': 200,
         'responsetime': '2023-05-08 18:30:23',
         'username': 'xxxxx',
         'wallet_before': '80.5',
         'wallet_after': 77,
         'information': '订单详情已发送至您的邮件地址：xxxxxxxxx@qq.com',
         'reservation': {
           'sid': '1056',
           'eid': '27472',
           'service': 'フジテレビ',
           'title': 'テレビアニメ「鬼滅の刃」刀鍛冶の里編[字][解][デ]',
           'starttime': '2023-05-14 23:15:00',
           'duration': '30',
           'price': '3.5',
           'resid': '25512',
           'orderid': '29373',
           'server': 0}
          }
        """
        self._last_resp = self._client.post(API.SUBSCRIBE,
                                            data={
                                                'token': self._token,
                                                'sid': sid,
                                                'eid': eid,
                                                'tsid': tsid,
                                                'onid': onid,
                                                'price': price,
                                                'network': network,
                                                'reservetoken': reservetoken
                                            },
                                            **kwargs)
        # assert status_code
        self._last_resp.raise_for_status()
        self.last_json = self._parse_json()
        self._raise_for_json_status('预约失败！')
        # on fail:
        # {'response_code': 403,
        #  'responsetime': '2023-05-08 18:32:31',
        #  'information': '本节目您已经预约过了，请不要重复预约'}
        if 'reservation' not in self.last_json:
            raise ApiException('预约结果响应信息格式错误！', response_json=self.last_json)
        try:
            reservation = Reservation(**self.last_json['reservation'])
        except Exception as e:
            raise ApiException('预约结果响应信息格式错误！' + str(e), response_json=self.last_json)

        return reservation

    def get_userinfo(self, **kwargs) -> UserInfo:
        """
        获取账户信息

        raise `ApiException` on fail

        Returns
        ---
        dict:
            With following keys:
            response_code	int	响应码
            responsetime	str	响应时间
            userinfo[]		array	用户信息
              -id			int	用户ID
              -username		str	用户名
              -password		str	密码
              -wallet		str	余额
              -email		str	用户邮箱
              -readnid		str	已读通知ID
              -online		str	Cookies生命标记
              -onlinetoken	str	用户API Token
              -lastip		str	上次登陆IP
              -lasttime		str	上次登录时间
              -times_draw	str	剩余抽奖次数

            Example:
            {'response_code': 200,
             'responsetime': '2023-05-08 18:05:55',
             'userinfo': {'id': 'xxx',
              'username': 'xxx',
              'password': 'xxx',
              'wallet': '80.5',
              'email': 'xxxxxxxx@qq.com',
              'readnid': None,
              'online': '1',
              'onlinetoken': 'xxxxxx',
              'lastip': 'xxx.xxx.64.208',
              'lasttime': '2023-05-08 18:05:52',
              'times_draw': '0'}}
        """
        self._last_resp = self._client.post(API.USERINFO,
                                            data={
                                                'token': self._token,
                                            },
                                            **kwargs)
        # assert status_code
        self._last_resp.raise_for_status()
        self.last_json = self._parse_json()
        # error example:
        # {'response_code': 401, 'responsetime': '2023-06-12 22:05:51', 'information': '鉴权失败，Token错误'}
        self._raise_for_json_status('获取用户信息失败！')
        if 'userinfo' not in self.last_json:
            raise ApiException('用户信息响应信息格式错误！', response_json=self.last_json)
        try:
            userinfo = UserInfo(**self.last_json['userinfo'])
        except Exception as e:
            raise ApiException('用户信息响应信息格式错误！' + str(e), response_json=self.last_json)

        return userinfo

    def get_order(self,
                  index: int = 1,
                  count: int = 15,
                  order: Literal['ASC', 'DESC'] = 'DESC',
                  air_date: str = None,
                  keyword: str = None,
                  username: str = None,
                  operator: str = None,
                  **kwargs):
        """
        获取预约列表

        raise `ApiException` on fail

        Parameters
        ---
        index: int
            请求起始页码
        count: int
            请求订单数量
        order: str
            请求排序方式（ASC，DESC）
        air_date: str
            放送日期，用于按日期查询。（API有bug暂无法使用）
        keyword: str
            按关键词查询（API有bug暂无法使用）
        username: str
            按用户名查询（API有bug暂无法使用）
        operator: str
            操作员用户名（API有bug暂无法使用）

        Returns
        ---
        dict:
            With following keys:
            response_code	int	响应码
            responsetime	str	响应时间
            date			str	按日期查询
            keyword			str	按关键词查询
            index			int	请求起始页码
            count			int	请求订单数量
            count_in_list	int	本次实际获得的订单数量
            reservations[]	array	订单列表
              -orderid		str	用户订单ID
              -resid		str	录制ID
              -service		str	频道名称
              -title		str	节目名称
              -starttime	str	播出时间
              -duration		str	时长（分钟）
              -reservetime	str	首次预约时间
              -sharelink	str	未经分段的分享链接
              -price		str	订单价格

            Example:
            {'response_code': 200,
             'responsetime': '2023-05-08 18:27:58',
             'date': None,
             'keyword': '|',
             'index': '1',
             'count': '1',
             'count_in_list': '79',
             'reservations': [{
               'orderid': '29391',
               'resid': '25333',
               'service': 'フジテレビ',
               'title': 'テレビアニメ「鬼滅の刃」刀鍛冶の里編[字][解][デ]',
               'category': '7',
               'detail': '第五話『赫刀』\nご案内\n【公式ＨＰ】\nhttps://www.fujitv.co.jp/kimetsu\n番組内容\n＜前回のあらすじ＞\n苦戦する禰豆子の元に駆けつけ、一進一退の攻防を繰り広げる炭治郎だったが、可楽による団扇の攻撃を受け、禰豆子と二人、気を失ってしまう。そのころ、金魚の鬼の群れが刀鍛冶たちに次々と襲い掛かり、里は危機に瀕（ひん）していた。その報せを聞いた蜜璃は、里の救出へ向かう――。\n番組内容２\n第五話『赫刀』は５月７日（日）２３時１５分放送！\n\n遊郭での任務を終えた炭治郎たちの次なる物語を描く「刀鍛冶の里編」。炭治郎が向かう先は、刀鍛冶の里。鬼殺隊最強の剣士≪柱≫である、霞柱・時透無一郎と恋柱・甘露寺蜜璃との再会、忍びよる鬼の影。炭治郎たちの新たな戦いが始まる。\n出演者\n竈門炭治郎（かまど・たんじろう）：\u3000花江夏樹\u3000\n竈門禰豆子（かまど・ねずこ）※：\u3000鬼頭明里\u3000\n時透無一郎（ときとう・むいちろう）：\u3000河西健吾\u3000\n甘露寺蜜璃（かんろじ・みつり）：\u3000花澤香菜\u3000\n不死川玄弥（しなずがわ・げんや）：\u3000岡本信彦\u3000\n\n半天狗（はんてんぐ）：\u3000古川登志夫\u3000\n玉壺（ぎょっこ）：\u3000鳥海浩輔\u3000\n\n※禰豆子の「禰」は「ネ＋爾」が正しい表記。\nスタッフ\n【主題歌】\n＜オープニングテーマ＞\nＭＡＮ\u3000ＷＩＴＨ\u3000Ａ\u3000ＭＩＳＳＩＯＮ×ｍｉｌｅｔ\u3000『絆ノ奇跡』\u3000\n＜エンディングテーマ＞\nｍｉｌｅｔ×ＭＡＮ\u3000ＷＩＴＨ\u3000Ａ\u3000ＭＩＳＳＩＯＮ\u3000『コイコガレ』\u3000\n\n【原作】\n吾峠呼世晴（集英社ジャンプ\u3000コミックス刊）\u3000\n【監督】\n外崎春雄\u3000\n【キャラクターデザイン・総作画監督】\n松島晃\u3000\n【脚本制作】\nｕｆｏｔａｂｌｅ\nスタッフ２\n【サブキャラクターデザイン】\n佐藤美幸、梶山庸子、菊池美花\u3000\n【プロップデザイン】\n小山将治\u3000\n【美術監督】\n衛藤功二\u3000\n【撮影監督】\n寺尾優一\u3000\n【３Ｄ監督】\n西脇一樹\u3000\n【色彩設計】\n大前祐子\u3000\n【編集】\n神野学\u3000\n【音楽】\n梶浦由記、椎名豪\u3000\n【アニメーション制作】\nｕｆｏｔａｂｌｅ\u3000\n【製作】\nアニプレックス、集英社、ｕｆｏｔａｂｌｅ\n',
               'starttime': '2023-05-07 23:15',
               'duration': '30',
               'reservetime': '2023-05-07 21:15',
               'sharelink': '链接: https://pan.baidu.com/s/1_DESLe3o_6LRq1fBPlru3w 提取码: hn8v',
               'price': '3.5'},...
               ]
             }
        """
        data = {
            'token': self._token,
            'index': index,
            'count': count,
            'order': order,
        }
        if air_date:
            data['date'] = air_date
        if keyword:
            data['keyword'] = keyword
        if username:
            data['username'] = username
        if operator:
            data['operator'] = operator

        self._last_resp = self._client.post(API.GET_ORDER, data=data, **kwargs)
        # assert status_code
        self._last_resp.raise_for_status()
        self.last_json = self._parse_json()
        self._raise_for_json_status('获取预约列表失败！')
        return self.last_json

    def is_online(self) -> bool:
        try:
            user = self.get_userinfo()
        except ApiException:
            return False
        return user.online == UserInfo.__ONLINE__

    def __repr__(self):
        return 'TVSubscriber("' + self._username + '")'
