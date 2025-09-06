import threading
from typing import List
from azure_speech.stt import speech_to_text_once
import asyncio
from llm_core.agent.orchestrater import red_alert_workflow_async
import argparse
from concurrent.futures import ThreadPoolExecutor
import sched
import time
from threading import Thread
from llm_core.runtime_game_state import GROUP_COMMANDER_MONITOR, schedule_monitor
import logging

logger = logging.getLogger("AgentSystem")


# Initialize ThreadPoolExecutor with max 1 workers
executor = ThreadPoolExecutor(max_workers=1)
MAX_ACTIVE_TASKS = 3

def convert_str_to_bool(arg: str) -> bool:
    return arg.lower() == "true"

# Wrap synchronous input() as an async function
async def get_input_async():
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, input, ">>> ")

# Wrap synchronous speech_to_text_once() as an async function
async def get_speech_input_async():
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, speech_to_text_once)

def run_scheduler_monitoring():
    # Initialize scheduler
    scheduler = sched.scheduler(time.time, time.sleep)
    # Schedule initial monitoring task with 3-second interval
    scheduler.enter(0, 1, schedule_monitor, (scheduler, 3))
    # Start scheduler in a daemon thread
    sched_thread = Thread(target=scheduler.run, daemon=True)
    sched_thread.start()
    logger.info("[INFO] 地图监控已启动")

def run_group_commander_monitor():
    GROUP_COMMANDER_MONITOR.start()
    logger.info("[INFO] 小队指挥监控已启动")


def run_workflow_in_thread(user_input: str):
    """
    在后台守护线程中运行 red_alert_workflow_async，并返回 (loop, task)。
    注意：task 属于子线程 loop，如需操作请用 loop.call_soon_threadsafe。
    """
    loop = asyncio.new_event_loop()
    task = loop.create_task(red_alert_workflow_async(user_input))

    def runner():
        try:
            loop.run_until_complete(task)
        except Exception as e:
            logger.info(f"Workflow error: {e}", exc_info=True)
        finally:
            loop.close()

    t = threading.Thread(target=runner, daemon=True)
    t.start()
    return loop, task


def cancel_task(loop: asyncio.AbstractEventLoop, task: asyncio.Task):
    """线程安全取消任务。"""
    if not task.done():
        loop.call_soon_threadsafe(task.cancel)


async def main(enable_speech: bool = True):
    # Start monitoring tasks
    run_group_commander_monitor()
    active_tasks: List[tuple[asyncio.AbstractEventLoop, asyncio.Task]] = []
    while True:
        user_input = None
        if enable_speech:
            logger.info("[INFO] 请开始说话...")
            user_input = await get_speech_input_async()
        else:
            logger.info("[INFO] 请输入指令...")
            user_input = await get_input_async()
        logger.info(f"[USER MISSION]: {user_input}")
        if user_input and "退出游戏" in user_input:
            logger.info("[INFO] 退出游戏中...")
            break

        if user_input:
            # Check if there are 3 active tasks
            active_tasks = [(lp, tk) for lp, tk in active_tasks if not tk.done()]
            while len(active_tasks) >= MAX_ACTIVE_TASKS:
                lp, tk = active_tasks.pop(0)
                cancel_task(lp, tk)

            # Submit new task to executor
            loop, task = run_workflow_in_thread(user_input)
            active_tasks.append((loop, task))
            

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='RA Copilot params')
    parser.add_argument('--enable_speech', type=str, help='是否运行Azure Speech来进行语音转文字。', default="false")
    args = parser.parse_args()
    enable_speech = convert_str_to_bool(args.enable_speech)
    asyncio.run(main(enable_speech))