import logging
from agents import HandoffInputData, handoff
from agents.extensions import handoff_filters


logger = logging.getLogger("AgentSystem")


# ===== handoff 过滤 =====
def handoff_message_tool_msg_filter(handoff_message_data: HandoffInputData) -> HandoffInputData:
    handoff_message_data = handoff_filters.remove_all_tools(handoff_message_data)
    history = handoff_message_data.input_history
    return HandoffInputData(
        input_history=history,
        pre_handoff_items=tuple(handoff_message_data.pre_handoff_items),
        new_items=tuple(handoff_message_data.new_items),
    )

def handoff_message_tool_msg_filter_list(agents:list) -> list:
    return [handoff(agent, input_filter=handoff_message_tool_msg_filter) for agent in agents]
