from agents import Agent
from azure_speech.stt import speech_to_text_once
import asyncio
import configs
from openai_mcp.mcp_client import create_executor_async, agent_chat_async
import argparse
from openai_mcp.agent.agent_factory import AgentFactory


def convert_str_to_bool(arg: str) -> bool:
    return arg.lower() == "true"


async def main(enable_speech:bool = True):
    async with create_executor_async(mcp_server_params=configs.MCP_CONFIGS.MCP_SERVER_PARAMS_LIST) as mcp_servers:
        # 代理实例
        war_executer = AgentFactory.create_attack_retreat_agent(mcp_servers=mcp_servers)
        executer = AgentFactory.create_executor_agent(mcp_servers=mcp_servers, handoffs=[war_executer])
        while True:
            user_input = None
            if enable_speech:
                print("[INFO] 请开始说话...")
                user_input = speech_to_text_once()
            else:
                print("[INFO] 请输入指令...")
                user_input = input(">>> ")
            print(f"[USER MISSION]: {user_input}")
            if user_input and "退出游戏" in user_input:
                break

            if user_input:
                await agent_chat_async(executer, war_executer, user_input)


if __name__ == "__main__":
    # 创建 ArgumentParser 对象
    parser = argparse.ArgumentParser(description='RA Copilot params')
    parser.add_argument('--enable_speech', type=str, help='是否运行Azure Speech来进行语音转文字。', default="true")
    args = parser.parse_args()
    enable_speech = convert_str_to_bool(args.enable_speech)
    asyncio.run(main(enable_speech))