import nonebot
from nonebot import on_command
from nonebot.adapters.cqhttp import Bot
from nonebot.adapters.cqhttp import MessageEvent, MessageSegment
from nonebot.typing import T_State
from nonebot.log import logger

from ...database import DB
from ...utils import get_type_id, permission_check, to_me, handle_uid

mua = nonebot.on_keyword({'mua'}, rule=to_me(), priority=5)

@mua.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State):
    content = "✋✋✋"
    if event.user_id == 534400134:
        content = "🥰mua😘😘"

    message = MessageSegment.at(event.user_id) + content
    await mua.finish(message)