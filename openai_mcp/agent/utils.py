from agents import HandoffInputData
from agents import HandoffInputData
from agents.extensions import handoff_filters


def handoff_message_tool_msg_filter(handoff_message_data: HandoffInputData) -> HandoffInputData:
    print("!!!!!!!! 即将切换为全面战争状态 !!!!!!!!!")
    # First, we'll remove any tool-related messages from the message history
    handoff_message_data = handoff_filters.remove_all_tools(handoff_message_data)

    # Second, we'll also remove the first two items from the history, just for demonstration
    history = handoff_message_data.input_history

    # or, you can use the HandoffInputData.clone(kwargs) method
    return HandoffInputData(
        input_history=history,
        pre_handoff_items=tuple(handoff_message_data.pre_handoff_items),
        new_items=tuple(handoff_message_data.new_items),
    )