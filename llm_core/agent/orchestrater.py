import traceback
from agents import ItemHelpers, Runner, TResponseInputItem, set_default_openai_api, set_default_openai_client, set_tracing_disabled
from openai import AsyncAzureOpenAI
import configs
from .utils import handoff_message_tool_msg_filter_list
from ..expert.task_classifier_expert import task_classifier_function
from llm_core.agent.agent_factory import AgentFactory
import logging
from ..expert.task_classifier_expert import AgentCategory
from ..tools.function_tools.game_tools import (
    build_unit, place_building, produce_units, deploy_mcv, manage_production, repair_units, query_game_state,
    move_units_by_location, form_group, query_group, stop_move, attack_target,
)
from ..tools.function_tools.squad_commander_tool import (
    squad_commander_tool, move_squad_by_location, stop_move_squad, squad_attack_enemy_actor, explore_map
)


logger = logging.getLogger("AgentSystem")


task_classifier_agent = AgentFactory.create_task_classification_agent()
building_agent = AgentFactory.create_building_agent()
squad_formation_agent = AgentFactory.create_format_squad_agent()
squad_commander_agent = AgentFactory.create_squad_commander_agent()
default_executer_agent = AgentFactory.create_executor_agent()

# workflow
task_classifier_agent.handoffs = handoff_message_tool_msg_filter_list([building_agent, squad_commander_agent, squad_formation_agent, default_executer_agent])
squad_formation_agent.handoffs = handoff_message_tool_msg_filter_list([squad_commander_agent])
squad_commander_agent.handoffs = handoff_message_tool_msg_filter_list([squad_formation_agent])


# functions
building_agent.tools = [build_unit, place_building, produce_units, deploy_mcv, manage_production, repair_units, query_game_state]
squad_formation_agent.tools = [form_group, query_group, query_game_state]
squad_commander_agent.tools = [squad_commander_tool, attack_target, move_squad_by_location, stop_move_squad, query_group, squad_attack_enemy_actor, explore_map, query_game_state]
default_executer_agent.tools = [build_unit, place_building, produce_units, deploy_mcv, manage_production, repair_units, query_game_state, move_units_by_location, form_group, query_group, stop_move, attack_target]

# function -> agent
AGENT_MAP = {
    AgentCategory.BUILD: building_agent,
    AgentCategory.FORMATION: squad_formation_agent,
    AgentCategory.SQUAD_LEADER: squad_commander_agent,
    AgentCategory.OTHER: default_executer_agent,
}


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

async def red_alert_workflow_async(query: str, max_turns: int = configs.AGENTS_CONFIGS.AGENT_REFLECTION_MAX_TURN, enable_task_classifier_agent: bool = True):
    """
    Workflow for Red Alert assistant bot using multi-agent handoff.
    - Starts with task classification agent to categorize and handoff the task.
    - Handoff to base_agent for base-related tasks (building, base vehicle movement).
    - Handoff to formation_agent for unit formation tasks.
    - For squad commands (attack/retreat/defend), dynamically create and manage multiple squad commander agents.
    """
    try:
        logger.info("[INFO] red_alert_workflow_async running")
        # with trace("RA executer and evaluator trace"):
        mission = "任务目标：在游戏中，" + query # 避免触发Azure OpenAI的ContentFilter功能
        input_items: list[TResponseInputItem] = [{"content": mission, "role": "user"}]

        agent = task_classifier_agent
        while max_turns > 0:
            # Step 0: Try Task Classifier Function
            if not enable_task_classifier_agent:
                agent = task_classifier_function(query, AGENT_MAP) 

            # Step 1: Run Task Classification Agent
            executer_response = await Runner.run(agent, mission, max_turns=configs.AGENTS_CONFIGS.SINGAL_AGENT_MAX_TURN)
            input_items = executer_response.to_input_list()
            latest_outline = ItemHelpers.text_message_outputs(executer_response.new_items)
            agent_feedback = executer_response.final_output
            if agent_feedback.task_complete.lower() == "completed":
                break

            input_items.append({"content": f"批准，请立刻调用tools。", "role": "user"})
            agent = executer_response.last_agent
            logger.info("[RE_RUN WITH APPROVING]")
            max_turns -= 1

        return executer_response.final_output
    
    except KeyboardInterrupt:
        logger.info("[INFO] 用户手动中断")

    except Exception as e:
        logger.info(f"[ERROR] 与助手交互时发生错误: {e}")
        traceback.print_exc()
        return None