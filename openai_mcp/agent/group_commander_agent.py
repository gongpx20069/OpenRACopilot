from dataclasses import dataclass
from typing import List, Literal
from agents import function_tool
from pydantic import Field
import configs
from OpenRA_Copilot_Library.models import Location
from ..runtime_game_state import GROUP_COMMANDER_MONITOR


# Group War State
@dataclass
class GroupWarState:
    war_state: Literal["attack", "defense", "retreat"] = Field(..., description="计划发起的战斗模式，攻击/防御附近可见敌人，或者及时撤退。")
    group_id: int = Field(..., description="选择军队队伍id（一定要编队后的）。")
    retreat_location: List[int] = Field(
        None, 
        description="撤退的安全位置（默认为己方建造厂附近），格式为 [x, y]，不能超出地图边界。",
        min_items=2,
        max_items=2,
        items={"type": "integer"}
    )


@function_tool(description_override=configs.AGENTS_CONFIGS.ATTACK_RETREAT_HANDOFF_DESCRIPTION, name_override="group_commander_tool")
def group_commander_tool(
    group_id: int = Field(..., description="选择军队队伍id（一定要编队后的）。"), 
    war_state: Literal["attack", "defense", "retreat"] = Field(..., description="计划发起的战斗模式，攻击/防御附近可见敌人，或者及时撤退。"), 
    retreat_location:List[int] = Field(
        None, 
        description="撤退的安全位置（默认为己方建造厂附近），格式为 [x, y]，不能超出地图边界。",
        min_items=2,
        max_items=2,
        items={"type": "integer"}
    )
    ) -> str:
    created = GROUP_COMMANDER_MONITOR.start_group(group_id=group_id, state=war_state, retreat_location=Location(retreat_location[0], retreat_location[1]))
    if not created:
        GROUP_COMMANDER_MONITOR.stop_group(group_id)
        GROUP_COMMANDER_MONITOR.start_group(group_id=group_id, state=war_state, retreat_location=Location(retreat_location[0], retreat_location[1]))
        print(f"小队{group_id}已经在战斗中，更新战斗模式为{GROUP_COMMANDER_MONITOR.get_group_state(group_id)}")
        return f"小队{group_id}已经在战斗中，更新战斗模式为{GROUP_COMMANDER_MONITOR.get_group_state(group_id)}"

    print(f"[INFO] 组织小队{group_id}，该小队进入{war_state}状态。")
    return f"已组织小队{group_id}，该小队进入{war_state}状态。**NOTE:立刻结束会话，以及时响应用户新的指令。**"


