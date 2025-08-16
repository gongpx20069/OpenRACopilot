from typing import List
from mcp.server.fastmcp import FastMCP
from pydantic import  Field
from OpenRA_Copilot_Library.game_api import GameAPIError
from OpenRA_Copilot_Library.models import Actor, TargetsQueryParam
from .utils import classify_different_faction_actors, validate_actor_ids, print_tool_io
from . import BUILDING, VEHICLE, INFANTRIES, AIR, game_api, UNIT_DEPENDENCIES, BUILDING_DEPENDENCIES
from collections import defaultdict
import traceback

# init game api
build_mcp = FastMCP(name="RedAlert Game Server - Building, Producing and Basic Info Part", port=8001)


@build_mcp.tool(name="build_unit", description="开始建造指定名称的建筑。")
@print_tool_io
def build_unit(
    building_name: str = Field(..., description="要建造的建筑中文名称，必须是以下列表中的一个：" + ", ".join(BUILDING)),
    ) -> str:
    if building_name not in BUILDING:
        return f"[ERROR] 未知的建筑名称: {building_name}"
    if not game_api.can_produce(building_name):
        if building_name in BUILDING_DEPENDENCIES:
            return f"[ERROR] 不能建造 {building_name}，该建筑的依赖为{BUILDING_DEPENDENCIES[building_name]}"
        else:
            return f"[ERROR] 不能建造 {building_name}，可调用其他工具查看当前可建造的资源列表。"
    game_api.produce_wait(unit_type=building_name, quantity=1, auto_place_building=True)
    return f"[SUCCESS] 建造 {building_name} 成功"


@build_mcp.tool(name="place_building", description="放置建造完成的建筑或者防御。")
@print_tool_io
def place_building(
    building_type: str = Field(..., description="要放置建造完成的建筑还是防御，必须为['建筑', '防御']中的一个")
    ) -> str:
    building_or_defense = "Building" if "建筑" in building_type else "Defense"
    building_queue = game_api.query_production_queue(building_or_defense)
    if building_queue and building_queue["queue_items"]:
        if building_queue["queue_items"][0]["status"].lower() == "completed":
            game_api.place_building(building_or_defense)
            return f"[SUCCESS] {building_queue['queue_items'][0]['unit_type']} 已放置"
        else:
            return f"[INFO] {building_or_defense} 在建造队列中，当前状态：{building_queue['queue_items'][0]['status']}"
    else:
        return f"[ERROR] {building_or_defense} 不在建造队列中"


@build_mcp.tool(name="produce_units", description="开始生产指定类型的士兵，载具，飞机或者海军")
@print_tool_io
def produce_units(
    unit_type: str = Field(..., description="要生产的单位类型，必须是以下列表中的一个：" + ", ".join(INFANTRIES + VEHICLE + AIR)),
    num: int = Field(..., description="要生产的单位数量"),
    ) -> str:
    if unit_type not in INFANTRIES + VEHICLE + AIR:
        return f"[ERROR] 未知的单位类型: {unit_type}"
    if not game_api.can_produce(unit_type):
        if unit_type in UNIT_DEPENDENCIES:
            return f"[ERROR] 不能生产 {unit_type}，该单位的依赖为{UNIT_DEPENDENCIES[unit_type]}"
        else:
            return f"[ERROR] 不能生产 {unit_type}，可调用其他工具查看当前可生产的资源列表。"
    game_api.produce(unit_type=unit_type, quantity=num, auto_place_building=False)
    return f"[SUCCESS] 生产 {unit_type} 成功，生产任务完成。"


@build_mcp.tool(name="deploy_mcv", description="部署基地车")
@print_tool_io
def deploy_mcv() -> str:
    mcv = game_api.query_actor(TargetsQueryParam(type=['mcv'], faction='自己'))
    if not mcv:
        return "[ERROR] 没有找到基地车"
    game_api.deploy_units(mcv)
    return f"[SUCCESS] 基地车已部署, 基地车基本信息如下: {mcv[0]}"


@build_mcp.tool(name="manage_production", description="管理（暂停/开始/取消）生产队列")
@print_tool_io
def manage_production(
    production_type: str = Field(..., description="要管理的生产类型，必须为['Building', 'Defense', 'Infantry', 'Vehicle', 'Aircraft', 'Naval']中的一个"), 
    action: str = Field(..., description="要执行的操作，必须为['pause','cancel','resume']中的一个")
) -> str:
    # 转换生产类型为API所需格式
    try:
        if production_type not in ['Building', 'Defense', 'Infantry', 'Vehicle', 'Aircraft', 'Naval']:
            return f"[ERROR] 无效的生产类型: {production_type}，必须为['Building', 'Defense', 'Infantry', 'Vehicle', 'Aircraft', 'Naval']中的一个"
        
        if action not in ['pause','cancel','resume']:
            return f"[ERROR] 无效的操作: {action}，必须为['pause','cancel','resume']中的一个"
        game_api.manage_production(queue_type=production_type, action=action)
        return f"[SUCCESS] 成功{action}{production_type}生产队列"
    except GameAPIError as e:
        return f"[ERROR] 操作失败: {e.message}"
    

@build_mcp.tool(name="repair_units", description="修复单位，可以是载具或者建筑，修理载具需要先修建修理中心。")
@print_tool_io
def repair_units(
    actor_ids: List[int] = Field(..., description="要修复的单位的actor id列表")
) -> str:
    try:
        validated_actors = validate_actor_ids(actor_ids)
        game_api.repair_units(actors=validated_actors)
        return f"[SUCCESS] 正在修复有效单位[{validated_actors}]"
    except:
        return "[ERROR] 修复出现问题，请确定ActorList中的ID是有效的己方载具或者建筑ID。"


# @build_mcp.tool(name="ensure_can_build", description="确保可以建造指定的建筑，如果不能会尝试生产所有前置建筑，并等待生产完成。")
# def ensure_can_build(
#     building_name: str = Field(..., description="要建造的建筑中文名称，必须是以下列表中的一个：" + ", ".join(BUILDING)),
# ) -> str:
#     if building_name not in BUILDING:
#         return f"[ERROR] 未知的建筑名称: {building_name}"
#     if game_api.ensure_can_build_wait(building_name=building_name):
#         return f"[SUCCESS] 建造{building_name}完成。"
#     return f"[ERROR] 建造{building_name}失败。"


@build_mcp.tool(name="query_game_state", description="查询游戏状态（所有自己的单位，地图信息，玩家基地信息，查询屏幕信息）")
@print_tool_io
def query_game_state() -> str:
    result = ""
    try:
        result = "# 地图上所有可见单位信息\n"

        # 查询所有自己的单位
        query_param = TargetsQueryParam()
        actors = game_api.query_actor(query_param)
        
        if actors:
            actor_faction_type_dict = classify_different_faction_actors(actors)
            for faction in actor_faction_type_dict:
                actor_faction = actor_faction_type_dict[faction]
                result += f"## {faction}单位详情：\n"        
                for actor_type in actor_faction:
                    result += f"{actor_type}类型的Actor信息如下：\n"
                    for actor in actor_faction[actor_type]:
                        result += f"- ID:{actor.actor_id} 位置:({actor.position.x},{actor.position.y}) HP:{actor.hppercent}%\n"
                    result += f"... {actor_type} 类型共有 {len(actor_faction[actor_type])} 个单位\n\n"
                result += "\n"

        produce_types = ['Building', 'Defense', 'Infantry', 'Vehicle', 'Aircraft'] # Naval 出现问题，暂时先排除
        result += "# 生产队列信息\n"
        for produce_type in produce_types:
            produce_queue = game_api.query_production_queue(queue_type=produce_type)
            result += f"## {produce_queue['queue_type']}生产队列信息\n"
            new_produce_queue = defaultdict(list)
            in_progress_item = produce_queue['queue_items'][0] if produce_queue['queue_items'] else None
            for item in produce_queue['queue_items']:
                new_produce_queue[item['chineseName']].append(item)

            # 正在建造的项目 - 第一个项目
            if in_progress_item:
                result += "### 正在建造的项目信息\n"
                result += f"- 项目名称：{in_progress_item['chineseName']} 单个项目状态：{in_progress_item['status']} 单个项目进度：{in_progress_item['progress_percent']}% 单个最少剩余时间：{in_progress_item['remaining_time']} 单个项目总时间：{in_progress_item['total_time']} 单个项目剩余花费：{in_progress_item['remaining_cost']} 单个项目总花费：{in_progress_item['total_cost']} 该项目是否暂停：{in_progress_item['paused']} 该项目是否完成：{in_progress_item['done']} 该项目数量{len(new_produce_queue[in_progress_item['chineseName']])} 所属建筑ID：{item['owner_actor_id']}\n"

            # 等待建造的项目
            if new_produce_queue:
                result += "### 等待建造的项目信息\n"
                for chineseName in new_produce_queue:
                    if chineseName != in_progress_item["chineseName"]:
                        item = new_produce_queue[chineseName][0]
                        result += f"- 项目名称：{item['chineseName']} 单个项目状态：{item['status']} 单个项目进度：{item['progress_percent']}% 单个最少剩余时间：{item['remaining_time']} 单个项目总时间：{item['total_time']} 单个项目剩余花费：{item['remaining_cost']} 单个项目总花费：{item['total_cost']} 该项目是否暂停：{item['paused']} 该项目是否完成：{item['done']} 该项目数量{len(new_produce_queue[chineseName])} 所属建筑ID：{item['owner_actor_id']}\n"
            result += "\n\n"
        result += "\n"
        
        # 查询地图信息
        result += "# 地图信息\n"
        map_info = game_api.map_query()
        result += f"- 宽度{map_info.MapWidth}\n"
        result += f"- 高度{map_info.MapHeight}\n"
        result += f"- 地形类型{map_info.Terrain[0][0] if map_info.Terrain else '未知'}\n"
        result += "\n"

        # 查询玩家基地信息
        result += "# 玩家基地信息\n"
        base_info = game_api.player_base_info_query()
        result += f"- 现金{base_info.Cash}\n"
        result += f"- 资源{base_info.Resources}\n"
        result += f"- 电力{base_info.Power}\n"
        result += f"- 电力消耗{base_info.PowerDrained}\n"
        result += f"- 电力供应{base_info.PowerProvided}\n"
        result += "\n"

        # 查询屏幕信息
        result += "# 屏幕信息\n"
        screen_info = game_api.screen_info_query()
        result += "- 屏幕左上角" + f"({screen_info.ScreenMin.x}, {screen_info.ScreenMin.y})" + "\n"
        result += "- 屏幕右下角" + f"({screen_info.ScreenMax.x}, {screen_info.ScreenMax.y})" + "\n"
        result += f"- 鼠标在屏幕上{screen_info.IsMouseOnScreen}\n"
        result += "- 鼠标位置" + f"({screen_info.MousePosition.x}, {screen_info.MousePosition.y})" + "\n"
        result += "\n"

    except GameAPIError as e:
        result = f"[ERROR] 查询操作失败: {e.code} - {e.message}\n"
        traceback.print_exc()
    except Exception as e:
        result = f"[ERROR] 查询操作异常: {e}\n"
        traceback.print_exc()
    return result


if __name__ == "__main__":
    # 添加父目录到Python路径
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    build_mcp.run(transport="sse")