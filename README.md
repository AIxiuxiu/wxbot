最近没项目，刚好同学问我有没有做过微信自动加群，所以就去了解了一下，找到了 `wxpy` python库。因为python只是自己稍微学了一点，所以就照着作者的代码自己学着玩玩，没想到晚了两天就把我的微信web端封掉了，可能是因为测试时调接口太过频繁，所以有些功能还没有测试完成。把写的代码上传到了 github ，虽然只有简单的功能，但也希望可以帮助大家从始构建一个属于自己的微信机器人

因为一些功能需要使用新内核分支 `new-core` 来完成，所以需要安装新内核分支 `new-core`

```shell
pip install -U git+https://github.com/youfou/wxpy.git@new-core
```

其它用到的库安装有如下：

```shell
# psutil
pip install psutil
# requests
pip install requests
# lxml
pip install lxml
```

要想运行机器人需要一些配置必须正确

* 账号昵称：bot_name
* 管理者名称： admins_name
* 管理群名称：admin_group_name
* 需要管理的群名称：group_name
* 名片的微信id 和 名称：card_wxid, card_name

配置完成就可以启动自己的微信机器人了。因为有些功能虽然写了，但因为被封所以没能测试完，请自行测试，如果有问题可以告诉我进行更改。

如果觉得 wxpy 有用请给作者[star](https://github.com/youfou/wxpy)
参考文档（当前是新分支，文档只能进行参考）[wxpy文档](http://wxpy.readthedocs.io/zh/latest/chats.html#id8) 
参考代码 [groups.py](https://gist.github.com/youfou/03c1e0204ac092f873730f51671ce0a8)
