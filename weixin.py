#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date    : 2017-9-20 09:45:49
# @Author  : ahl 
# @Link    : http://example.org
# @Version : 1.0.0

import os
import re
import pdb
import random
import time
import datetime
import subprocess

#pip install psutil
import psutil

from functools import wraps
from pprint import pformat
from collections import Counter

# pip install requests
import requests

# pip install lxml
from lxml import etree

from tempfile import NamedTemporaryFile

# pip3 install -U git+https://github.com/youfou/wxpy.git@new-core
from wxpy import *
from wxpy.utils import ensure_list, start_new_thread

#  黑名单 和 投票踢人 
from kick_votes import KickVotes
from timed_list import TimedList

# ------------------------------------ 配置开始 ------------------------------------

# 开启缓存功能 缓存路径
cache_path = 'static/wx.pkl'

# 终端中是否显示登陆二维码 ,True 需要安装 pillow 模块 (pip3 install pillow)
console_qr = False

# 二维码存储路径
qr_path = 'static/qrcode.png'

#---------------必须正确存在的配置------------#

# 机器人昵称 (防止登错账号) 
bot_name = 'wxpy'

# 管理者名称元组 (如果包含机器人自己则最少两个管理员，否则无法建群) 
admins_name = ('wxpy', 'other')

# 管理群名称
admin_group_name = 'admin'

# 需要管理的群 必须存在 ，当群满时会创建（测试 + 群个数）的群
group_name = '测试'

# 发送名片的微信id 和 名称 (名片必须为好友关系或已关注的公众号)
card_wxid , card_name = 'wxid_xxxx', 'xx'


#---------------必须正确存在的配置结束------------#

# 自动回复模式 默认 图灵（tl）小i（xi）动图（dt）
reply_type = 'tl'

# 自动回复模式关键词
kw_reply_type = {
    'tl': (
        '图灵', 'tuling', 'tl'
    ),
    'xi': (
        '小i', 'xiaoi', 'xi'
    ),
    'dt': (
        '动图', 'dongtu', 'dt'
    )
}

# 自动回复模式对应回答
text_reply_type = {
    'tl': '图灵正在为您服务',
    'xi': '小i在在为您服务',
    'dt': '现在是动图模式'
}

# 自动回答关键词
kw_replies = {
    'wxpy 项目主页:\ngithub.com/youfou/wxpy': (
        '项目', '主页', '官网', '网站', 'github', '地址', '版本'
    ),
    'wxpy 在线文档:\nwxpy.readthedocs.io': (
        '请问', '文档', '帮助', '怎么', '如何', '请教', '安装', '说明'
    ),
    '必看: 常见问题 FAQ:\nwxpy.readthedocs.io/faq.html': (
        '常见', '问题', '问答', '什么', 'faq'
    )
}

# 图灵 key
TULING_KEY = 'f0f679cd576a4f6e8f917c692e7cd35e'
# 动图抓取地址
doutu_url = 'https://www.doutula.com/search'
# 动图抓取 xpath
xpath = '//div[contains(@class,"pic-content")][1]//img[contains(@class,"img-responsive")]/@data-original'

#自动添加好友的条件
addfriend_keywords = ('加好友', '加群')

# 入群口令
group_code = '加群'

# 群最大人数
GROUP_MAX = 100

# 最大受邀次数
INVITE_MAX = 3

# 新人入群的欢迎语
welcome_text = '🎉 欢迎 @{} 的加入！'

# 帮助
help_info = '''😃 讨论主题
· 本群主题为测试群
⚠️ 注意事项
· 严禁灰产/黑产相关内容话题
· 请勿发布对群员无价值的广告
👮 投票移出
· 移出后将被拉黑 24 小时
· 请在了解事因后谨慎投票
· 命令格式: "移出 @人员"
'''

# ------------------------------------- 配置结束 --------------------------------------

# 重启
def _restart():
    os.execv(sys.executable, [sys.executable] + sys.argv)

# 新人入群通知
def new_member(core, member):
    if member.group in groups:
        member.group.send(welcome_text.format(member.name))

# 踢除群通知
def deleting_member(core, member):
    if member.group in groups:
        admin_group.send('{0.name} 已离开群: {1.name}'.format(member, member.group))


bot = Bot(cache_path=cache_path, console_qr=console_qr, qr_path=qr_path, hooks=dict(
    new_member=new_member,
    deleting_member=deleting_member,
))

if bot.name != bot_name:
    logging.error('账号错误!')
    bot.logout()
    _restart()

# 获得一个专用 Logger
# 当不设置 `receiver` 时，会将日志发送到随后扫码登陆的微信的"文件传输助手"
logger = get_wechat_logger(bot, level=logging.INFO)

# 启用 puid 属性，并指定 puid 所需的映射数据保存/载入路径
#bot.enable_puid()

# 机器人账号自身
# myself = bot.self
# 在 Web 微信中把自己加为好友
# myself.add()
# myself.accept()

# 发送消息给自己
#myself.send('能收到吗？')


# my_friend = bot.friends.search('华')[0]
# logger.info('my_friend:{}'.format(my_friend.name))

# 管理者
#admins = bot.friends.get(remark_name='admin')
admins = list(map(lambda x: bot.friends.search(nickname=x)[0], admins_name))

# 管理群
admin_group = bot.groups.get(admin_group_name)

# 需要管理的群
groups = bot.groups.search(group_name)

# 远程踢人命令: 移出 @<需要被移出的人>
rp_kick = re.compile(
    # 普通踢人命令
    r'^(?:移出|移除|踢出)\s*@(?P<name_to_kick>.+?)(?:\u2005?\s*$)|'
    # 详细踢人命令:
    '^👉 复制移出 \(#(?P<option_id>\d+)\)\n'
    # 真实昵称
    '真实昵称: (?P<nickname>.+?)\n'
    # 群内昵称
    '(?:群内昵称: (?P<display_name>.+?)\n)?'
    # 省份 / 城市 / 性别
    '(?P<province>.+?) / (?P<city>.+?) / (?P<sex>.+?)'
    # 签名
    '(?:\n签名: (?P<signature>.+))?$'
)

# 投票 5分钟有效
kick_votes = KickVotes(300)

# 投票多少个则踢出
votes_to_kick = 5

# 黑名单
black_list = TimedList()

#-----------------------------------------工具类--------------------------------------

# 判断消息是否为支持回复的消息类型
def supported_msg_type(msg, reply_unsupported=False):
    supported = (TEXT,)
    ignored = (UNKNOWN, NOTICE, NEW_FRIEND)

    fallback_replies = {
        VOICE: '🙉',
        IMAGE: '🙈',
        VIDEO: '🙈',
    }

    if msg.type in supported:
        return True
    elif reply_unsupported and (msg.type not in ignored):
        msg.reply(fallback_replies.get(msg.type, '🐒'))

# 限制频率: 指定周期 period_secs 内超过 limit_msgs 条消息，直接回复 "🙊"  超过 black_limit 条则拉入黑名单 1 个小时
def freq_limit(period_secs=20, limit_msgs=5, black_limit=10, limit_secs=1*3600):
    def decorator(func):
        @wraps(func)
        def wrapped(msg):
            if msg.chat in black_list:
                return

            now = datetime.datetime.now()
            period = datetime.timedelta(seconds=period_secs)
            recent_received = 0
            for m in msg.bot.messages[::-1]:
                if m.sender == msg.sender:
                    if now - m.create_time > period:
                        break
                    recent_received += 1

            if recent_received > black_limit:
                black_list.set(msg.chat, limit_secs)
                return '你说得好快，我都累了，休息一下吧'
            elif recent_received > limit_msgs:
                if not isinstance(msg.chat, Group) or msg.is_at:
                    return '🙊'
            return func(msg)

        return wrapped

    return decorator

# 判断 msg 的发送者是否为管理员
def from_admin(msg):
    from_user = msg.member if isinstance(msg.chat, Group) else msg.sender
    return from_user in admins

# 装饰器 验证函数的第 1 个参数 msg 是否来自 admins
def admin_auth(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        msg = args[0]
        if from_admin(msg):
            return func(*args, **kwargs)
        else:
            raise ValueError('{} is not an admin!'.format(msg))

    return wrapped

# 用迭代的方式发送多条消息 
def send_iter(receiver, iterable):
    if isinstance(iterable, str):
        raise TypeError

    for msg in iterable:
        receiver.send(msg)

#------------------------------------工具类结束--------------------------------


#------------------------------------进程状态---------------------------------------

process = psutil.Process()

# 进程状态
def _status_text():
    uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(process.create_time())
    memory_usage = process.memory_info().rss
    memory_usage_percent = process.memory_percent()

    if globals().get('bot'):
        messages = bot.messages
    else:
        messages = list()

    return '[当前时间] {now:%H:%M:%S}\n[启动时长] {uptime}\n[使用内存] {memory}（{percent}）\n[接收消息] {messages}'.format(
        now=datetime.datetime.now(),
        uptime=str(uptime).split('.')[0],
        memory='{:.2f} MB'.format(memory_usage / 1024 ** 2),
        percent = '{:.1f} %'.format(memory_usage_percent),
        messages= '{} 条'.format(len(messages))
    )

def status_text():
    yield _status_text()

# 定时报告进程状态
def heartbeat():
    while bot.alive:
        time.sleep(600)
        try:
            send_iter(admin_group, status_text())
        except:
            logger.exception('failed to report heartbeat:\n')


start_new_thread(heartbeat)

send_iter(admin_group, status_text())

#------------------------------------进程状态结束-------------------------------------

#--------------------------------------自动回复---------------------------------------

# 改变自动回复方式
def change_reply_type(msg):
    global reply_type
    for r_type, keywords in kw_reply_type.items():
        for kw in keywords:
            if kw == msg.text.lower():
                reply_type = r_type
                msg.reply(text_reply_type[r_type])
                return True

# 根据关键词回复
def reply_by_keyword(msg):
    for reply, keywords in kw_replies.items():
        for kw in keywords:
            if msg.text and kw in msg.text.lower():
                msg.reply(reply)
                return True

# 使用图灵机器人自动聊天
tuling = Tuling(api_key=TULING_KEY)
def tl(msg):
    tuling.do_reply(msg)

# 使用小 i 机器人自动聊天
xiaoi = XiaoI('RFDSvMi0nwPB', 'fVi66ANWpPlBisf56BJH')
def xi(msg):
    xiaoi.do_reply(msg)

# 使用动图聊天
def dt(msg):
    res = requests.get(doutu_url, {'keyword': msg.text})
    html = etree.HTML(res.text)
    urls = html.xpath(xpath)
    url = random.choice(urls)
    fileType = url.rsplit('.', 1)[-1]
    while fileType != 'gif':
        url = random.choice(urls)
        fileType = url.rsplit('.', 1)[-1]

    res = requests.get(url, allow_redirects=False)
    tmp = NamedTemporaryFile()
    tmp.write(res.content)
    tmp.flush()
    media_id = bot.upload_file(tmp.name)
    tmp.close()
    msg.reply_image('.gif', media_id=media_id)    

# 自动添加好友
def addfriend(msg):
    for kw in addfriend_keywords:
        if kw in msg.text.lower():
            user = msg.card.accept()
            return True

# 自动回复名片 若消息包含"名片"，则回复名片 还有问题
def reply_send_card(msg):
    if '名片' in msg.text:
        pdb.set_trace()
        # 需修改代码为chat.py 151行代码 isinstance(friend_or_mp, Chat) core.py 652行 if msg_type in (TEXT, CARD): 
        msg.sender.send_card(card_wxid, card_name)
        logging.info('发送了名片: {}'.format(card_name))

        return True

#---------------------------------------自动回复结束------------------------------------

#------------------------------------------加群--------------------------------------

# 验证入群口令
def valid(msg):
    return group_code in str(msg.text).lower()

# 自动选择未满的群
def get_group(user):
    groups.sort(key=len, reverse=True)  # 用长度进行排序，从大到小进行排序
    for _group in groups:
        if len(_group) < GROUP_MAX:
            return _group
    else:
        logger.warning('群都满啦！')
        next_topic = group_name + str(len(groups) + 1)  #在群的名字后面+群个数
        pdb.set_trace()
        new_group = bot.create_group([*admins, user], topic=next_topic)
        admin_group.send('系统自动创建群: {}'.format(next_topic))
        return new_group

# 计算每个用户被邀请的次数
invite_counter = Counter()

# 邀请入群
def invite(user):
    joined = list()
    for group in groups:
        if user in group:
            joined.append(group)
    if joined:
        joined_group_names = '\n'.join(map(lambda x: x.name, joined))
        logger.info('{} is already in\n{}'.format(user, joined_group_names))
        user.send('你已加入了\n{}'.format(joined_group_names))
    else:
        if invite_counter.get(user, 0) < INVITE_MAX:
            group = get_group(user)
            user.send('验证通过 [嘿哈]')
            group.add(user, use_invitation=True)
            invite_counter.update([user])
        else:
            user.send('你的受邀次数已达最大限制 😷')

#----------------------------------------加群结束-------------------------------------

#-------------------------------------远程命令---------------------------------

# 更新群信息
def update_groups():
    yield '更新群信息'
    for _group in groups:
        _group.update()
        yield '{}: {}'.format(_group.name, len(_group))

# 重启
def restart():
    yield '重新启动中....'
    bot.core.dump()
    _restart()

# 获取延时
def latency():
    yield '当前延时：{:.2f}'.format(bot.messages[-1].latency)

# 远程命令 (单独发给机器人的消息)
remote_orders = {
    'g': update_groups,
    's': status_text,
    'r': restart,
    'l': latency,
}

# 执行 shell 命令
def remote_shell(command):     
    logger.info('执行远程 shell 命令:\n{}'.format(command))
    r = subprocess.run(
        command, shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    if r.stdout:
        yield r.stdout
    else:
        yield '[OK]'

# 执行 Python 代码
def remote_eval(source):
    try:
        ret = eval(source, globals())
    except (SyntaxError, NameError):
        raise ValueError('got SyntaxError or NameError in source')

    logger.info('执行远程eval:\n{}'.format(source))
    yield pformat(ret)

@admin_auth
def server_mgmt(msg):
    """
    服务器管理:
        若消息文本为为远程命令，则执行对应函数
        若消息文本以 ! 开头，则作为 shell 命令执行
        若不满足以上，则尝试直接将 msg.text 作为 Python 代码执行
    """
    order = remote_orders.get(msg.text.strip())
    if order:
        logger.info('远程命令: {}'.format(order.__name__))
        send_iter(msg.chat, order())
    elif msg.text.startswith('!'):
        command = msg.text[1:]
        send_iter(msg.chat, remote_shell(command))
    else:
        send_iter(msg.chat, remote_eval(msg.text))

# ------------------------------------远程命令结束----------------------------------

#--------------------------------------投票踢人-----------------------------------

# 尝试发送消息给指定聊天对象
@dont_raise_response_error
def try_send(chat, msg):
    if chat.is_friend:
        chat.send(msg)

# 踢出并加入黑名单
def _kick(to_kick, limit_secs=0, msg=None):
    if limit_secs:
        # 加入计时黑名单
        black_list.set(to_kick, limit_secs)

    to_kick.remove()
    start_new_thread(try_send, kwargs=dict(chat=to_kick, msg=msg))

    ret = '@{} 已被成功移出! 😈'.format(to_kick.name)

    if to_kick in kick_votes:
        voters = kick_votes[to_kick][0]
        voters = '\n'.join(map(lambda x: '@{}'.format(x.name), voters))
        ret += '\n\n投票人:\n{}'.format(voters)

    return

# 根据被踢人名称获取精准命令
def gen_detailed_kicks(found):
    yield '🤔 找到了 {} 个 "{}" \n👇 请精准选择，复制并发送'.format(len(found), found[0].name)
    for option_index, member in enumerate(found):
        option_text = '👉 复制移出 (#{})\n'.format(option_index + 1)
        option_text += '真实昵称: {}\n'.format(member.nickname)
        if member.display_name:
            option_text += '群内昵称: {}\n'.format(member.display_name)
        option_text += '{} / {} / {}'.format(
            member.province or '未知',
            member.city or '未知',
            {MALE: '男', FEMALE: '女'}.get(member.sex, '未知'))
        if member.signature:
            option_text += '\n签名: {}'.format(member.signature)

        yield option_text

# 进行投票踢人
def remote_kick(msg):
    info_msg = '抱歉，你已被{}移出，接下来的 24 小时内，机器人将对你保持沉默 😷'
    # 黑名单限制时间 24 小时
    limit_secs = 3600 * 24

    info = rp_kick.match(msg.text).groupdict()

    if info['name_to_kick']:
        # 简单命令
        found = msg.chat.search(name=info['name_to_kick'])

        if not found:
            return '查无此人，突然改名了吗 🤔'
        elif len(found) > 1:
            send_iter(msg.chat, gen_detailed_kicks(found))
            return
        else:
            member_to_kick = found[0]

    elif info['nickname']:
        # 详细命令
        info['sex'] = {'男': MALE, '女': FEMALE}.get(info['sex'])
        for attr in 'province', 'city':
            if info[attr] == '未知':
                info[attr] = None

        attributions = dict()
        for attr in 'nickname', 'display_name', 'province', 'city', 'sex', 'signature':
            attributions[attr] = info[attr]

        logger.info('detailed kick: {}'.format(attributions))
        found = msg.chat.search(**attributions)

        if not found:
            return '查无此人，难道又改名了 🤔'
        elif len(found) > 1:
            return '然而还是有重复的，呼叫群主本体吧...[捂脸]'
        else:
            member_to_kick = found[0]

    else:
        return

    if member_to_kick in admins:
        logger.error('{} tried to kick {} whom was an admin'.format(
            msg.member.name, member_to_kick.name))
        return '无法移出管理员 @{} 😷️'.format(member_to_kick.name)

    if from_admin(msg):
        # 管理员: 直接踢出
        return _kick(member_to_kick, limit_secs, info_msg.format('管理员'))
    else:
        # 其他群成员: 投票踢出
        votes, secs_left = kick_votes.vote(voter=msg.member, to_kick=member_to_kick)

        now = time.time()
        voted = 0
        for voters, start in kick_votes.votes.values():
            if msg.member in voters and now - start < 600:
                # 10 分钟内尝试投票移出 3 个群员，则认为是恶意用户
                voted += 1
                if voted >= 3:
                    _kick(msg.member, limit_secs, '抱歉，你因恶意投票而被移出。接下来的 24 小时内，机器人将对你保持沉默 [悠闲]')
                    return '移出了恶意投票者 @{} '.format(msg.member.name)

        if votes < votes_to_kick:

            voting = '正在投票移出 @{name}{id}' \
                     '\n当前 {votes} / {votes_to_kick} 票 ({secs_left:.0f} 秒内有效)' \
                     '\n移出将拉黑 24 小时 😵' \
                     '\n请谨慎投票 🤔'

            return voting.format(
                name=member_to_kick.name,
                id=' (#{})'.format(info['option_id']) if info['option_id'] else '',
                votes=votes,
                votes_to_kick=votes_to_kick,
                secs_left=secs_left)

        else:
            return _kick(member_to_kick, limit_secs, info_msg.format('投票'))

#-------------------------------------投票踢人结束----------------------------------

#------------------------------------ bot处理消息 --------------------------------

# 自动回复自己
@bot.register(bot.self, except_self=False)
def reply_my_self(msg):
    if supported_msg_type(msg, reply_unsupported=True):
        if not reply_by_keyword(msg):
            if not change_reply_type(msg):
                reply = eval(reply_type)
                reply(msg)

# 响应好友消息，限制频率 (需要放前面)
@bot.register(Friend, TEXT)
@freq_limit()
def exist_friends(msg):
    if msg.chat in black_list:
        return
    if valid(msg):
        invite(msg.sender)
    elif not reply_send_card(msg):
        reply_by_keyword(msg)

# 响应好友请求
@bot.register(msg_types=NEW_FRIEND)
def new_friend(msg):
    if msg.card in black_list:
        return
    if addfriend(msg):
        if valid(msg):
            invite(user)

# 自动添加好友失败后，手动加为好友后自动发送消息
@bot.register(Friend, NOTICE, except_self=False)
def manually_added(msg):
    if not get_revoked():
        if '现在可以开始聊天了' in msg.text:
            time.sleep(2)
            for group in groups:
                if msg.chat in group:
                    break
            else:
                if msg.chat not in invite_counter:
                    return '你好呀，{}，还记得咱们的入群口令吗？回复口令即可获取入群邀请。'.format(msg.chat.name)


# 将撤回信息转发到机器人的文件传输助手
@bot.register(msg_types=RECALLED)
def get_revoked_msg(msg):
    pdb.set_trace()
    # 根据找到的撤回消息 id 找到 bot.messages 中的原消息
    revoked_msg = bot.messages.search(id=msg.recalled_id)[0]
    # 原发送者 (群聊时为群员)
    sender = msg.member or msg.sender
    # 把消息转发到文件传输助手
    revoked_msg.forward(bot.file_helper, prefix='{} 撤回了:'.format(sender.name))


# 在其他群中回复被 @ 的消息
# @bot.register(Group, TEXT)
# def reply_other_group(msg):
#     if msg.chat not in groups and msg.is_at:
#         if supported_msg_type(msg, reply_unsupported=True):
#             tuling.do_reply(msg)


# 响应远程管理员
@bot.register(admin_group, msg_types=TEXT, except_self=False)
def reply_admins(msg):
    try:
        server_mgmt(msg)
    except ValueError:
        # 以上不满足或尝试失败，则作为普通聊天内容回复
        if isinstance(msg.chat, User):
            return exist_friends(msg)

# 群的消息处理 
@bot.register(groups, msg_types=TEXT, except_self=False)
def wxpy_group(msg):
    if rp_kick.match(msg.text):
        return remote_kick(msg)
    elif msg.text.lower().strip() in ('帮助', '说明', '规则', 'help'):
        return help_info

# 群发出系统通知时激活群数据的更新 (有新消息时才会更新)
@bot.register(groups, NOTICE) 
def group_notice(msg):
    admin_group.send('{}:\n{}'.format(msg.chat, msg.text))

#---------------------------------- bot处理结束 --------------------------------

#pdb.set_trace()

embed()
