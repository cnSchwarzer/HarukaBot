import asyncio
import traceback
from datetime import datetime, timedelta
import json
from nonebot.log import logger
from pathlib import Path

from ...libs.weiboreq import WeiboReq
from ...database import DB
from ...libs.weibo import Weibo
from ...utils import safe_send, scheduler, get_weibo_screenshot
from nonebot.adapters.cqhttp.message import MessageSegment

last_time = {}
j = Path("weibo_pull.json")
if j.exists():
    try:
        last_time = json.loads(j.read_text('utf-8'))
    except:
        last_time = {}

logger.info(f'weibo pull state {last_time}')

cookie_path = Path('./weibo.cookie')

@scheduler.scheduled_job('interval', seconds=5, id='weibo_sched')
async def wb_sched():
    """微博推送"""
    cookie = None
    if cookie_path.exists():
        cookie = json.loads(cookie_path.read_text('utf-8').strip())
        logger.debug('加载微博 Cookie')
        logger.debug(cookie)
    else:
        logger.error('未发现微博 Cookie: ./weibo.cookie')

    if cookie is None:
        logger.debug('未发现微博 Cookie, 跳过')
        return

    async with DB() as db:
        uid = await db.next_uid('weibo')
        if not uid:
            return
        user = await db.get_user(uid)
        assert user is not None
        name = user.name
        weibo_id = str(user.weibo_id)

    logger.debug(f'爬取微博 {name}（{weibo_id}, {uid}）')
    wr = WeiboReq(cookie)
    weibos = await wr.get_user_weibo(weibo_id)
    if weibos is None:
        return
    weibos = weibos.get('list', [])

    if len(weibos) == 0:  # 没有发过动态或者动态全删的直接结束
        return

    if weibo_id not in last_time:  # 没有爬取过这位主播就把最新一条动态时间为 last_time
        weibo = Weibo(weibos[0])
        last_time[weibo_id] = weibo.time
        j.write_text(json.dumps(last_time))
        return

    for weibo in weibos[4::-1]:  # 从旧到新取最近5条动态
        weibo = Weibo(weibo)
        if weibo.time > last_time[weibo_id]:
            logger.info(f"检测到新微博（{weibo.id}）：{name}（{weibo_id}, {uid}）")

            await weibo.format()

            async with DB() as db:
                push_list = await db.get_push_list(uid, 'weibo')
                for sets in push_list:
                    await safe_send(sets.bot_id, sets.type, sets.type_id, weibo.message, sets.at)

            image = None
            for _ in range(3):
                try:
                    image = await get_weibo_screenshot(weibo.url, cookie)
                    break
                except Exception as e:
                    logger.error("截图失败")
                    #logger.error(traceback(e))
                await asyncio.sleep(0.1)
            if not image:
                logger.error("已达到重试上限，将在下个轮询中重新尝试")

            async with DB() as db:
                push_list = await db.get_push_list(uid, 'weibo')
                for sets in push_list:
                    await safe_send(sets.bot_id, sets.type, sets.type_id, MessageSegment.image(f"base64://{image}"))

            last_time[weibo_id] = weibo.time
            j.write_text(json.dumps(last_time))
