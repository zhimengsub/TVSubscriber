import datetime
from typing import Optional, Union

from pydantic import BaseModel, Field

from tvsubscriber.utils.const import NETWORKS


class Channel(BaseModel):
    """频道"""
    service: str
    """频道名称"""
    sid: int = Field(strict=False)
    """频道SID"""
    tsid: Optional[int] = Field(default=None, strict=False)
    """频道TSID"""
    epgtoken: Optional[str] = None
    """请求EPG需要的token。可以被刷新，因此设为Optional"""
    network: NETWORKS
    """频道所属网络"""

    def __hash__(self):
        return hash((self.service, self.network, self.sid))

    def __eq__(self, other):
        # be careful with isinstance! packages imported from different levels would result in false.
        return (
            hasattr(other, 'service') and
            hasattr(other, 'sid') and
            hasattr(other, 'tsid') and
            hasattr(other, 'network') and
            self.service == other.service and
            self.sid == other.sid and
            (self.tsid is None and other.tsid is None or self.tsid == other.tsid) and
            self.network == other.network
        )


class Event(BaseModel):
    """节目"""
    __FORMAT_STARTDATE__ = '%Y/%m/%d'
    """节目播出日期解析格式"""
    __FORMAT_STARTTIME__ = '%H:%M:%S'
    """节目开始时间解析格式"""
    sid: int = Field(strict=False)
    """频道SID"""
    tsid: int = Field(strict=False)
    """频道TSID"""
    onid: int = Field(strict=False)
    """频道ONID"""
    eid: int = Field(strict=False)
    """节目EID"""
    service: str
    """频道名称"""
    startdate: datetime.date
    """节目播出日期"""
    starttime: datetime.time
    """节目开始时间"""
    timestamp: datetime.datetime
    """节目开始时间戳"""
    week: str
    """星期（0-6）"""
    week_text: str
    """曜日（日月火水木金土）"""
    duration: float
    """时长（分钟）"""
    event_name: str
    """节目名称"""
    event_text: str
    """节目说明"""
    event_ext_text: str
    """节目补充说明"""
    category: Optional[str]
    """节目分类（英语）"""
    resolution: str
    """播出分辨率（1080i，480i）"""
    network: NETWORKS
    """频道所属网络（Kanto，Kansai，Nagoya，BS，CS）"""
    price: Union[int, float] = Field(strict=False)
    """价格"""
    reservetoken: str
    """预约需要的token"""

    def __init__(self, *, startdate: str, starttime: str, **kwargs):
        try:
            startdate = datetime.datetime.strptime(startdate, self.__FORMAT_STARTDATE__).date()
        except ValueError:
            startdate = datetime.datetime.strptime(startdate, '%Y-%m-%d').date()
        starttime = datetime.datetime.strptime(starttime, self.__FORMAT_STARTTIME__).time()
        super().__init__(startdate=startdate, starttime=starttime, **kwargs)

    def __hash__(self):
        return hash((self.network, self.sid, self.tsid, self.onid, self.eid, self.price))

    def __eq__(self, other):
        # be careful with isinstance! packages imported from different levels would result in false.
        if (
            hasattr(other, 'eid') and
            hasattr(other, 'sid') and
            hasattr(other, 'tsid') and
            hasattr(other, 'onid') and
            hasattr(other, 'price') and
            hasattr(other, 'network')
        ):
            return (
                self.eid == other.eid and
                self.sid == other.sid and
                self.tsid is None and other.tsid is None or self.tsid == other.tsid and
                self.onid == other.onid and
                self.price == other.price and
                self.network == other.network
            )
        return False


class Reservation(BaseModel):
    """预约结果"""
    __FORMAT_STARTTIME__: str = '%Y-%m-%d %H:%M:%S'
    """节目开始时间解析格式"""
    sid: int = Field(strict=False)
    """频道SID"""
    eid: int = Field(strict=False)
    """节目EID"""
    service: str
    """频道名称"""
    starttime: datetime.datetime
    """节目开始日期时间"""
    duration: Union[int, float] = Field(strict=False)
    """时长（分钟）"""
    price: Union[int, float] = Field(strict=False)
    """价格"""
    resid: int = Field(strict=False)
    """预约ID"""
    orderid: int = Field(strict=False)
    """订单ID"""
    server: int
    """已预约服务器编号"""
    def __init__(self, *, starttime: str, **kwargs):
        starttime = datetime.datetime.strptime(starttime, self.__FORMAT_STARTTIME__)
        super().__init__(starttime=starttime, **kwargs)


class UserInfo(BaseModel):
    """用户信息"""
    __ONLINE__: str = '1'
    """在线状态"""
    __FORMAT_LASTTIME__: str = '%Y-%m-%d %H:%M:%S'
    """上次登录时间解析格式"""
    id: int
    """用户ID"""
    username: str
    """用户名"""
    password: str
    """密码"""
    wallet: str
    """余额"""
    email: str
    """用户邮箱"""
    readnid: Optional[str] = None
    """已读通知ID"""
    online: str
    """Cookies生命标记"""
    onlinetoken: str
    """用户API Token"""
    lastip: Optional[str] = None
    """上次登陆IP"""
    lasttime: Optional[datetime.datetime] = None
    """上次登录日期时间"""
    times_draw: Optional[str] = None
    """剩余抽奖次数"""
    def __init__(self, *, lasttime: str, **kwargs):
        lasttime = datetime.datetime.strptime(lasttime, self.__FORMAT_LASTTIME__)
        super().__init__(lasttime=lasttime, **kwargs)
