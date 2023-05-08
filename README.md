# TVSubscriber

片源录制接口适配

## 配置与使用

按照`configs_template.json`的格式新建一个`configs.json`，设置用户名和密码。

具体使用请自行查看`TVSubscriber.py`内的注释，总的来说需要从`login()`开始依次调用。

```python
from TVSubscriber import TVSubscriber

username = 'xxx'
password = 'xxx'

subscriber = TVSubscriber()
subscriber.login(username, password)
```

