from dataclasses import dataclass
from typing import Callable, List, Literal
from agents import Agent, Handoff, handoff
from agents.mcp import MCPServer
from pydantic import Field
import configs
from .utils import handoff_message_tool_msg_filter

# Global State
@dataclass
class GlobalState:
    war_state: Literal["in_war", "not_in_war"] = Field(..., description="当前全局战争状态")


# Feedback 类
@dataclass
class EvaluationFeedback:
    feedback: str = Field(..., description="对副指挥官的决策进行选择和回复，保持精简")
    task_complete: Literal["completed", "not_completed"] = Field(..., description="任务是否完成")


@dataclass
class ExecutorFeedback:
    feedback: str = Field(..., description="任务执行反馈")
    task_complete: Literal["completed", "in_progress"] = Field(..., description="当前任务进度")
    # change_to_war_status: bool = Field(..., description="是否需要进入战时状态（攻击/撤退时的状态）")


@dataclass
class AttackRetreatFeecback:
    war_status: Literal["exit", "still_in"] = Field(..., description="当前战争状态")
    reason: str = Field(..., description="为什么退出战时状态")


## 构造 Agent 工厂类
class AgentFactory:
    @staticmethod
    def create_evaluator_agent() -> Agent:
        # --- 构造 Evaluation Agent 的函数 ---
        return Agent(
            name = "Red Alert指挥官",
            instructions=configs.AGENTS_CONFIGS.EVALUATION_INSTRUCTION,
            model=configs.AGENTS_CONFIGS.EVALUATOR_AOAI_DEPLOYMENT,
            output_type=EvaluationFeedback,
        )
    
    @staticmethod
    def create_executor_agent(mcp_servers:List[MCPServer] = [], handoff_agents:List[Agent] = [], tools:List[Callable] = []) -> Agent:
        # --- 构造 Executer Agent 的函数 ---
        return Agent(
            model=configs.AGENTS_CONFIGS.EXECUTER_AOAI_DEPLOYMENT,
            name="RedAlert Executor",
            instructions=configs.AGENTS_CONFIGS.EXECUTER_INSTRUCTION,
            mcp_servers=mcp_servers,
            output_type=ExecutorFeedback,
            handoffs=[handoff(agent, input_filter=handoff_message_tool_msg_filter) for agent in handoff_agents],
            tools=tools,
            )
    
    
    @staticmethod
    def create_attack_retreat_agent(mcp_servers:List[MCPServer] = []) -> Agent:
        # --- 构造 Attack Retreat Agent 的函数 ---
        return Agent(
            model=configs.AGENTS_CONFIGS.ATTACK_RETREAT_AOAI_DEPLOYMENT,
            name="RedAlert War Executor",
            handoff_description=configs.AGENTS_CONFIGS.ATTACK_RETREAT_HANDOFF_DESCRIPTION,
            instructions=configs.AGENTS_CONFIGS.ATTACK_RETREAT_INSTRUCTION,
            mcp_servers=mcp_servers,
            output_type=AttackRetreatFeecback,
        )