from dataclasses import dataclass
from typing import AsyncGenerator, List, Literal
from openai import AsyncAzureOpenAI
from agents import (
    Agent, 
    Runner, 
    set_default_openai_client, 
    set_default_openai_api, 
    enable_verbose_stdout_logging, 
    trace,
    set_tracing_disabled,
    TResponseInputItem, 
    ItemHelpers,
    )
from agents.mcp import MCPServerSse, MCPServerSseParams
from pydantic import Field
import configs
import traceback
from contextlib import asynccontextmanager
from .agent.agent_factory import ExecutorFeedback, AttackRetreatFeecback


# enable_verbose_stdout_logging()
set_tracing_disabled(True)
set_default_openai_api("chat_completions")
set_default_openai_client(
    AsyncAzureOpenAI(
        base_url=configs.AOAI_CONFIGS.AOAI_ENDPOINT,
        azure_deployment=configs.AOAI_CONFIGS.AOAI_DEPLOYMENT,
        api_key=configs.AOAI_CONFIGS.AOAI_APIKEY,
        api_version=configs.AOAI_CONFIGS.AOAI_API_VERSION,
        )
    )


# --- 构造 async context manager ---
@asynccontextmanager
async def create_executor_async(mcp_server_params: List[dict] = [{"url": "http://127.0.0.1:8000/sse"}]) -> AsyncGenerator[List[MCPServerSse], None]:
    """
    构造 Agent 实例并配置 MCP SSE 服务器，并连接
    """
    mcp_servers = [
        MCPServerSse(
            cache_tools_list=True,
            params=MCPServerSseParams(**param),
            client_session_timeout_seconds=param.get("timeout", 5)
        )
        for param in mcp_server_params
    ]

    print("Connecting to all MCP servers...")
    for server in mcp_servers:
        await server.connect()
        print(f"MCP Tools {server.name}: ", await server.list_tools())
    print("All MCP servers connected.")
    try:
        yield mcp_servers # yield 代理实例
    finally:
        # 退出 with 块时，手动断开所有 MCP 服务器连接
        print("Disconnecting from all MCP servers...")
        for server in mcp_servers: await server.cleanup()
        print("All MCP servers disconnected.")


async def agent_chat_async(agent: Agent, attack_agent:Agent, query: str, max_turns: int = configs.AGENTS_CONFIGS.AGENT_REFLECTION_MAX_TURN):
    # 构造 Agent 实例
    try:
        # with trace("RA executer and evaluator trace"):
        mission = "任务目标：在游戏中，" + query # 避免触发Azure OpenAI的ContentFilter功能
        input_items: list[TResponseInputItem] = [{"content": mission, "role": "user"}]
        while max_turns > 0:
            executer_response = await Runner.run(agent, mission, max_turns=configs.AGENTS_CONFIGS.SINGAL_AGENT_MAX_TURN)

            input_items = executer_response.to_input_list()
            latest_outline = ItemHelpers.text_message_outputs(executer_response.new_items)
            agent_feedback = executer_response.final_output
            if isinstance(agent_feedback, ExecutorFeedback):
                print("[RA EXECUTER REASONING]:", latest_outline)
                if agent_feedback.task_complete.lower() == "completed":
                    break
            elif isinstance(agent_feedback, AttackRetreatFeecback):
                print("[RA WAR EXECUTER REASONING]:", latest_outline)
                while agent_feedback.war_status.lower() == "still_in":
                    input_items.append({"content": f"批准，请立刻执行", "role": "user"})
                    executer_response = await Runner.run(attack_agent, mission, max_turns=configs.AGENTS_CONFIGS.SINGAL_AGENT_MAX_TURN)
                    input_items = executer_response.to_input_list()
                    latest_outline = ItemHelpers.text_message_outputs(executer_response.new_items)
                    agent_feedback = executer_response.final_output
                    print("[RA WAR EXECUTER REASONING]:", latest_outline)
                print("[RA WAR EXECUTER EXITED]:", agent_feedback.reason)
                break

            input_items.append({"content": f"批准，请立刻执行", "role": "user"})
            print("Re-running with feedback")
            max_turns -= 1

        return executer_response.final_output
    
    except KeyboardInterrupt:
        print("[INFO] 用户手动中断")

    except Exception as e:
        print(f"[ERROR] 与助手交互时发生错误: {e}")
        traceback.print_exc()
        return None