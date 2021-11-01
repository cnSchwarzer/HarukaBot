import asyncio
import signal
import traceback
from datetime import datetime, timedelta
from nonebot.log import logger
import subprocess
from ..utils import scheduler

cq = subprocess.Popen(["./go-cqhttp", 'faststart'])
logger.success(f"go-cqhttp pid={cq.pid}")


# restart cqhttp every 30 minutes
@scheduler.scheduled_job('interval', seconds=1800, id='cq')
def cq_sched():
    global cq
    cq.send_signal(signal.CTRL_C_EVENT)
    cq.send_signal(signal.SIGTERM)
    cq = subprocess.Popen(["./go-cqhttp", 'faststart'])
    logger.success(f"go-cqhttp pid={cq.pid}")
