from typing import List
from mcp.server.fastmcp import FastMCP
from pydantic import  Field
from OpenRA_Copilot_Library.game_api import GameAPIError
from OpenRA_Copilot_Library.models import Actor, Location, TargetsQueryParam
from . import BUILDING, VEHICLE, INFANTRIES, AIR, game_api
from .utils import validate_actor_ids, print_tool_io, tool_sleep
import traceback


# init game api
actor_mcp = FastMCP(name="RedAlert Game Server - Moving and Attacking Part", port=8000)


@actor_mcp.tool(name="move_units_by_location", description="开始移动单位（载具，士兵，空军，海军）到指定位置。")
@tool_sleep(0.6)
@print_tool_io
def move_units_by_location(
    actor_ids: List[int] = Field(..., description="计划移动的单位ID列表"),
    location: List[int] = Field(
        ..., 
        description="目标位置，格式为 [x, y]，不能超出地图边界。",
        min_items=2,
        max_items=2,
        items={"type": "integer"}
    ),
    attack_move: bool = Field(False, description="是否边移动边攻击"),
):
    try:
        validated_actors = validate_actor_ids(actor_ids)
        location = Location(x=location[0], y=location[1])
        game_api.move_units_by_location(validated_actors, location, attack_move)
        return f"[SUCCESS] 正在移动Actor [{validated_actors}] 到目标位置{location}中"
    except:
        return "[ERROR] 移动出现问题，请确定ActorList中的ID是有效的己方有效（载具，士兵，空军，海军）ID。"


@actor_mcp.tool(name="form_group", description="将单位（载具，士兵，空军，海军）编成具体的组。")
@print_tool_io
def form_group(
    actor_ids: List[int] = Field(..., description="计划组织的单位ID列表"),
    group_id: int = Field(..., description="计划编队后的ID")
):
    try:
        validated_actors = validate_actor_ids(actor_ids)
        game_api.form_group(validated_actors, group_id)
        return f"[SUCCESS] 正在将Actor [{validated_actors}] 组织成组{group_id}"
    except:
        return "[ERROR] 无法编队，请确定ActorList中的ID是有效的己方有效（载具，士兵，空军，海军）ID。"
    

@actor_mcp.tool(name="query_group", description="查询某个具体的编队有哪些具体单位（载具，士兵，空军，海军）。")
@print_tool_io
def query_group(
    group_id: int = Field(..., description="想要查询的我方军事单位编组ID")
):
    try:
        result = f"# 编组{group_id}\n"
        group = game_api.query_actor(query_params=TargetsQueryParam(group_id=[group_id]))
        for actor in group:
            result += f"- ID：{actor.actor_id}，类型：{actor.type}，位置：{actor.position}，HP：{actor.hppercent}%\n"
        result += f"...编组{group_id}共{len(group)}个单位。\n"
        return result
    except Exception as ex:
        print(ex)
        traceback.print_exc()
        return f"[ERROR] 无法查询编组，请确定编组ID是有效的"
    

@actor_mcp.tool(name="stop_move", description="停止单位（载具，士兵，空军，海军）的移动。")
@print_tool_io
def stop_move(
    actor_ids: List[int] = Field(..., description="计划停止移动的单位ID列表"),
):
    try:
        validated_actors = validate_actor_ids(actor_ids)
        game_api.stop(validated_actors)
        return f"[SUCCESS] 正在停止Actor [{validated_actors}] 的移动"
    except:
        return "[ERROR] 无法停止移动，请确定ActorList中的ID是有效的己方有效（载具，士兵，空军，海军）ID。"
    

@actor_mcp.tool(name="attack_target", description="组织单位（载具，士兵，空军，海军）攻击目标。")
@print_tool_io
def attack_target(
    actor_ids: List[int] = Field(..., description="单位ID列表"),
    target_id: int = Field(..., description="攻击目标定的Actor Id"),
):
    try:
        target_actor = Actor(actor_id=target_id)
        if game_api.can_attack_target(target=target_actor):
            validated_actors = validate_actor_ids(actor_ids)
            for actor in validated_actors:
                game_api.attack_target(actor, target_actor)

            return f"[SUCCESS] Actor [{validated_actors}] 正在攻击目标 {target_id}"
        else:
            return f"[ERROR] 目标无法攻击，请确定攻击目标{target_id}存在"
    except:
        return "[ERROR] 无法攻击，请确定ActorList中的ID是有效的己方有效（载具，士兵，空军，海军）ID。"
    

@actor_mcp.tool(name="occupy_units", description="使用工程师占领中立建筑或者敌方建筑（需先削弱至黄血 / 红血状态，30%生命值以下）。")
@print_tool_io
def occupy_units(
    actor_ids: List[int] = Field(..., description="工程师Actor ID列表"),
    target_id: int = Field(..., description="占领目标的Actor ID"),
):
    try:
        validate_actors = validate_actor_ids(actor_ids=actor_ids)
        game_api.occupy_units(occupiers=validate_actors, targets=[Actor(actor_id=target_id)])
        return f"[SUCCESS] 正在占领目标 {target_id}"
    except:
        return f"[ERROR] 无法占领，请确定ActorList中的ID {validate_actors}是有效的己方有效工程师Actor ID。"