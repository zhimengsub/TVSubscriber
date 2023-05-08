from pydantic import BaseModel


class Channel(BaseModel):
    """频道"""
    service: str
    """频道名称"""
    sid: str
    """频道SID"""
    tsid: str = None
    """频道TSID"""
    epgtoken: str
    """请求EPG需要的token"""


class Event(BaseModel):
    """节目"""
    sid: str
    """频道SID"""
    tsid: str
    """频道TSID"""
    onid: str
    """频道ONID"""
    eid: str
    """节目EID"""
    service: str
    """频道名称"""
    startdate: str
    """节目播出日期"""
    starttime: str
    """节目开始时间"""
    timestamp: int
    """节目开始时间戳"""
    week: str
    """星期（0-6）"""
    week_text: str
    """曜日（日月火水木金土）"""
    duration: int
    """时长（分钟）"""
    event_name: str
    """节目名称"""
    event_text: str
    """节目说明"""
    event_ext_text: str
    """节目补充说明"""
    category: str
    """节目分类（英语）"""
    resolution: str
    """播出分辨率（1080i，480i）"""
    network: str
    """频道所属网络（Kanto，Kansai，Nagoya，BS，CS）"""
    price: float
    """价格"""
    reservetoken: str
    """预约需要的token"""


class Reservation(BaseModel):
    """预约结果"""
    sid: str
    """频道SID"""
    eid: str
    """节目EID"""
    service: str
    """频道名称"""
    starttime: str
    """节目开始时间"""
    duration: str
    """时长（分钟）"""
    price: float
    """价格"""
    resid: str
    """预约ID"""
    orderid: str
    """订单ID"""
    server: int
    """已预约服务器编号"""
