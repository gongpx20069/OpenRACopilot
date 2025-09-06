from typing import List, Literal
from agents import function_tool
from pydantic import Field

from ...expert.group_commander_expert import AttackState
from ... import game_api
import logging
from OpenRA_Copilot_Library.models import Actor, Location, TargetsQueryParam
from ...runtime_game_state import GROUP_COMMANDER_MONITOR
from ..utils import print_tool_io


logger = logging.getLogger("AgentSystem")


@function_tool(description_override="发现了敌人并且将小队全体单位按照自动化算法投入战斗，小队进入进攻/防御/撤退模式", name_override="auto_war_tool")
@print_tool_io
def squad_commander_tool(
    group_id: int = Field(..., description="选择小队id。"), 
    war_state: Literal["attack", "defense", "retreat"] = Field(..., description="计划将小队全体单位投入的战斗模式，攻击/防御附近可见敌人，或者及时撤退。- attck:消灭小队附近所有的敌军有生力量，包括其防御塔，军队，坦克，飞机和建筑; - defense:消灭小队附近敌军可作战的单位，包括其防御塔，军队，坦克和飞机（但不包括敌方建筑）; - retreat:立刻停止攻击并撤退到指定位置."), 
    retreat_location:List[int] = Field(
        None, 
        description="撤退的安全位置（默认为己方建造厂附近），格式为 [x, y]，不能超出地图边界。",
        min_items=2,
        max_items=2,
        items={"type": "integer"}
    )
    ) -> str:
    """
    组织小队进入战斗模式。
    """
    created = GROUP_COMMANDER_MONITOR.start_group(group_id=group_id, state=war_state, retreat_location=Location(retreat_location[0], retreat_location[1]))
    if not created:
        if GROUP_COMMANDER_MONITOR.change_group_state(group_id=group_id, state=war_state, retreat_location=Location(retreat_location[0], retreat_location[1])):
            logger.info(f"小队{group_id}已经在战斗中，更新战斗模式为{GROUP_COMMANDER_MONITOR.get_group_state(group_id)}")
            return f"小队{group_id}已经在战斗中，更新战斗模式为{GROUP_COMMANDER_MONITOR.get_group_state(group_id)}"
        else:
            logger.info(f"小队{group_id}不存在")
            return f"小队{group_id}不存在"

    logger.info(f"[INFO] 组织小队{group_id}，该小队进入{war_state}状态。")
    return f"已组织小队{group_id}，该小队进入{war_state}状态。**NOTE:立刻结束会话，以及时响应用户新的指令。**"


@function_tool(description_override="将小队移动到指定位置", name_override="move_squad_by_location")
@print_tool_io
def move_squad_by_location(
    group_id: int = Field(..., description="打算移动的小队id。"), 
    location: List[int] = Field(
        ..., 
        description="目标位置，格式为 [x, y]，不能超出地图边界。",
        min_items=2,
        max_items=2,
        items={"type": "integer"}
    ),
    attack_move: bool = Field(False, description="是否边移动边攻击"),
) -> str:
    """
    组织小队移动到指定位置。
    """
    GROUP_COMMANDER_MONITOR.stop_group(group_id=group_id)
    group = game_api.query_actor(query_params=TargetsQueryParam(group_id=[group_id]))
    if group:
        game_api.move_units_by_location(actors=group, location=Location(x=location[0], y=location[1]), attack_move=attack_move)
        return f"[SUCCESS] 正在移动小队{group_id}到目标位置{location}中"
    else:
        return f"[WARNING] 小队{group_id}不存在"
    

@function_tool(description_override="将小队向指定位置移动并探索地图，如果遇到敌人则进入指定进攻/防御/撤退策略", name_override="move_explore_map_with_war_strategy")
@print_tool_io
def explore_map(
    group_id: int = Field(..., description="打算移动的小队id。"), 
    location: List[int] = Field(
        ..., 
        description="目标位置，格式为 [x, y]，不能超出地图边界。",
        min_items=2,
        max_items=2,
        items={"type": "integer"}
    ),
    war_strategy: Literal["attack", "defense", "retreat"] = Field("defense", description="如果遇到敌人，全体小队将立刻进入如下模式：- attck:消灭小队附近所有的敌军有生力量，包括其防御塔，军队，坦克，飞机和建筑; - defense:消灭小队附近敌军可作战的单位，包括其防御塔，军队，坦克和飞机（但不包括敌方建筑）; - retreat:立刻停止攻击并撤退到最初开始探路的起点."), 
) -> str:
    """
    组织小队移动到指定位置。
    """
    group = game_api.query_actor(query_params=TargetsQueryParam(group_id=[group_id]))
    if group:
        retreat_location = group[0].position
        created = GROUP_COMMANDER_MONITOR.start_group(group_id=group_id, state=AttackState.SCOUT, scout_on_enemy_strategy=war_strategy, retreat_location=retreat_location, scout_location=Location(location[0], location[1]))
        if not created:
            logger.info(f"小队{group_id}已经在战斗中，战斗模式为{GROUP_COMMANDER_MONITOR.get_group_state(group_id)}，无法更改为探路模式，可以使用撤退模式指挥小队撤退到指定位置。")
            return f"小队{group_id}已经在战斗中，战斗模式为{GROUP_COMMANDER_MONITOR.get_group_state(group_id)}，无法更改为探路模式，可以使用撤退模式指挥小队撤退到指定位置。"
        else:
            return f"小队{group_id}正在探索地图，目标位置为{location}，如果遇到敌人立刻切换为{war_strategy}策略"
    else:
        return f"[WARNING] 小队{group_id}不存在"


@function_tool(description_override="小队停止移动/停止攻击/停止一切正在的行动", name_override="stop_move_squad")
@print_tool_io
def stop_move_squad(group_id: int = Field(..., description="打算停止移动的小队id。")) -> str:
    """
    组织小队停止移动。
    """
    GROUP_COMMANDER_MONITOR.stop_group(group_id=group_id)
    group = game_api.query_actor(query_params=TargetsQueryParam(group_id=[group_id]))
    if group:
        game_api.stop(actors=group)
        return f"[SUCCESS] 小队{group_id}已停止移动"
    else:
        return f"[WARNING] 小队{group_id}不存在"
    

@function_tool(description_override="全体小队集中火力攻击敌方某一单位", name_override="squad_attack_enemy_actor")
@print_tool_io
def squad_attack_enemy_actor(
    group_id: int = Field(..., description="选择小队id。"), 
    enemy_actor_id: int = Field(..., description="选择敌人id。"), 
) -> str:
    """
    组织小队攻击敌人。
    """
    GROUP_COMMANDER_MONITOR.stop_group(group_id=group_id)
    group = game_api.query_actor(query_params=TargetsQueryParam(group_id=[group_id]))
    if group:
        for actor in group:
            game_api.attack_target(attacker=actor, target=Actor(actor_id=enemy_actor_id))
        return f"[SUCCESS] 小队{group_id}已开始攻击敌人{enemy_actor_id}"
    else:
        return f"[WARNING] 小队{group_id}不存在"