from azure_speech.stt import speech_to_text_once
import asyncio
import configs
from llm_core.tools.function_tools.squad_commander_tool import squad_commander_tool
from llm_core.mcp_client import create_executor_async, agent_chat_async
import argparse
from llm_core.agent.agent_factory import AgentFactory
from concurrent.futures import ThreadPoolExecutor
import sched
import time
from threading import Thread
from llm_core.runtime_game_state import GROUP_COMMANDER_MONITOR, schedule_monitor
import logging

logger = logging.getLogger("AgentSystem")
executor = ThreadPoolExecutor(max_workers=1)


def convert_str_to_bool(arg: str) -> bool:
    return arg.lower() == "true"


# 将同步的 input() 封装为异步函数
async def get_input_async():
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, input, ">>> ")

# 将同步的 speech_to_text_once() 封装为异步函数
async def get_speech_input_async():
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, speech_to_text_once)


def run_scheduler_monitoring():
    # 初始化调度器
    scheduler = sched.scheduler(time.time, time.sleep)
    
    # 设置初始监控任务，间隔3秒
    scheduler.enter(0, 1, schedule_monitor, (scheduler, 3))
    
    # 启动调度器线程
    sched_thread = Thread(target=scheduler.run, daemon=True)
    sched_thread.start()
    logger.info("[INFO] 地图监控已启动")


def run_group_commander_monitor():
    GROUP_COMMANDER_MONITOR.start()
    logger.info("[INFO] 组指挥监控已启动")


async def main(enable_speech:bool = True):
    # 启动地图监控
    # run_scheduler_monitoring()
    run_group_commander_monitor()
    async with create_executor_async(mcp_server_params=configs.MCP_CONFIGS.MCP_SERVER_PARAMS_LIST) as mcp_servers:
        # 代理实例
        # war_executor = AgentFactory.create_attack_retreat_agent(mcp_servers=mcp_servers)
        general_executor = AgentFactory.create_executor_agent(mcp_servers=mcp_servers, tools=[squad_commander_tool])
        while True:
            user_input = None
            if enable_speech:
                logger.info("[INFO] 请开始说话...")
                user_input = await get_speech_input_async()
            else:
                logger.info("[INFO] 请输入指令...")
                user_input = input(">>> ")
            logger.info(f"[USER MISSION]: {user_input}")
            if user_input and "退出游戏" in user_input:
                break

            if user_input:
                await agent_chat_async(general_executor, None, user_input)


if __name__ == "__main__":
    # 创建 ArgumentParser 对象
    parser = argparse.ArgumentParser(description='RA Copilot params')
    parser.add_argument('--enable_speech', type=str, help='是否运行Azure Speech来进行语音转文字。', default="false")
    args = parser.parse_args()
    enable_speech = convert_str_to_bool(args.enable_speech)
    asyncio.run(main(enable_speech))