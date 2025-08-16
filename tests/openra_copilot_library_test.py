#!/usr/bin/env python3
"""
from: https://github.com/OpenRA-CopilotTestGroup/OpenRA/blob/ea7c1b5bce82a243b48080f271a67dd5780820f2/Copilot/openra_ai/OpenRA_Copilot_Library/tests/real_test.py
真实的GameAPI测试脚本
直接调用GameAPI并输出实际结果，用于肉眼判断
"""

import sys
import os
import time
import json

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from OpenRA_Copilot_Library import GameAPI, GameAPIError, Location, Actor, TargetsQueryParam

def print_separator(title):
    """打印分隔符"""
    print("\n" + "=" * 60)
    print(f"🔍 {title}")
    print("=" * 60)

def print_result(title, result):
    """打印结果"""
    print(f"\n📋 {title}:")
    print("-" * 40)
    if isinstance(result, (dict, list)):
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result)
    print("-" * 40)

def test_server_connection():
    """测试服务器连接"""
    print_separator("测试服务器连接")
    
    try:
        # 检查服务器是否运行
        is_running = GameAPI.is_server_running("localhost", 7445, 2.0)
        print_result("服务器运行状态", is_running)
        
        if is_running:
            print("✅ 服务器正在运行")
        else:
            print("❌ 服务器未运行")
            return False
            
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False
    
    return True

def test_camera_operations(game_api: GameAPI):
    """测试相机操作"""
    print_separator("测试相机操作")
    
    try:
        # 测试按位置移动相机
        location = Location(32, 10)
        print(f"📷 移动相机到位置: {location}")
        game_api.move_camera_by_location(location)
        print("✅ 相机位置移动成功")
        time.sleep(1)
        
        print("📷 移动相机到单位位置")
        sample_actor = Actor(328)
        game_api.update_actor(sample_actor)
        print(sample_actor.position)
        game_api.move_camera_by_location(sample_actor.position)
        print("✅ 相机位置移动成功")
        time.sleep(1)
        
        
        # 测试按方向移动相机
        print("📷 向上移动相机10个单位")
        game_api.move_camera_by_direction("上", 10)
        print("✅ 相机方向移动成功")
        time.sleep(1)
        
        # 测试向右移动相机
        print("📷 向右移动相机15个单位")
        game_api.move_camera_by_direction("右", 15)
        print("✅ 相机方向移动成功")
        time.sleep(1)
        
        print(" 向左下移动13个单位")
        game_api.move_camera_by_direction("左下",13) 
        print("✅ 相机方向移动成功")
        time.sleep(1)
        
    except GameAPIError as e:
        print(f"❌ 相机操作失败: {e.code} - {e.message}")
    except Exception as e:
        print(f"❌ 相机操作异常: {e}")

def test_building_operations(game_api: GameAPI):
    """测试建筑操作"""
    print_separator("测试建筑操作")
    
    try:
        # 1. 展开基地车
        print("🏗️ 展开基地车...")
        game_api.deploy_mcv_and_wait(1.0)
        print("✅ 基地车展开完成")
        time.sleep(1)
        
        # 2. 建造电厂
        print("🏗️ 建造电厂...")
        build_success = False
        if game_api.ensure_can_build_wait("电厂"):
            wait_id = game_api.produce("电厂", 1)
            if wait_id:
                    success = game_api.wait(wait_id, 15.0)
                    if success:
                        print("✅ 电厂建造完成")
                        build_success = True
        if not build_success:
            print("❌ 电厂建造失败")
        
        # 3. 建造兵营
        print("🏗️ 建造兵营...")
        if game_api.ensure_can_build_wait("兵营"):
            wait_id = game_api.produce("兵营", 1)
            if wait_id:
                    success = game_api.wait(wait_id, 15.0)
                    if success:
                        print("✅ 兵营建造完成")
                        build_success = True
        if not build_success:
            print("❌ 兵营建造失败")
        
        # 4. 生产3个步兵
        print("🏭 生产3个步兵...")
        if game_api.ensure_can_produce_unit("步兵"):
            print("✅ 可以生产步兵，开始生产...")
            
            # 生产3个步兵
            wait_id = game_api.produce("步兵", 3)
            if wait_id:
                success = game_api.wait(wait_id, 15.0)
                if success:
                    print(f"✅ 步兵生产完成")
                else:
                    print(f"⏰ 步兵生产超时")
            else:
                print(f"❌ 步兵生产任务创建失败")
            time.sleep(1)
        else:
            print("❌ 无法生产步兵")
        
        # 5. 查询当前单位数量
        print("\n📊 查询当前单位情况...")
        all_units = game_api.query_actor(TargetsQueryParam(faction="自己"))
        infantry_units = game_api.query_actor(TargetsQueryParam(faction="自己", type=["步兵"]))
        building_units = game_api.query_actor(TargetsQueryParam(faction="自己", type=["电厂", "兵营"]))
        
        print_result("单位统计", {
            "总单位数": len(all_units),
            "步兵数量": len(infantry_units),
            "建筑数量": len(building_units)
        })
        
        if infantry_units:
            print("📋 步兵详情:")
            for i, infantry in enumerate(infantry_units):
                print(f"  {i+1}. ID:{infantry.actor_id} 位置:({infantry.position.x},{infantry.position.y}) HP:{infantry.hppercent}%")
        
    except GameAPIError as e:
        print(f"❌ 建筑操作失败: {e.code} - {e.message}")
    except Exception as e:
        print(f"❌ 建筑操作异常: {e}")

def test_query_operations(game_api):
    """测试查询操作"""
    print_separator("测试查询操作")
    
    try:
        # 查询所有自己的单位
        print("🔍 查询所有自己的单位...")
        query_param = TargetsQueryParam(faction="自己")
        actors = game_api.query_actor(query_param)
        print_result("查询到的单位数量", len(actors))
        
        if actors:
            print("📋 单位详情:")
            for i, actor in enumerate(actors[:5]):  # 只显示前5个
                print(f"  {i+1}. ID:{actor.actor_id} 类型:{actor.type} 位置:({actor.position.x},{actor.position.y}) HP:{actor.hppercent}%")
            if len(actors) > 5:
                print(f"  ... 还有 {len(actors)-5} 个单位")
        
        # 查询地图信息
        print("\n🗺️ 查询地图信息...")
        map_info = game_api.map_query()
        print_result("地图信息", {
            "宽度": map_info.MapWidth,
            "高度": map_info.MapHeight,
            "地形类型": map_info.Terrain[0][0] if map_info.Terrain else "未知"
        })
        
        # 查询玩家基地信息
        print("\n🏠 查询玩家基地信息...")
        base_info = game_api.player_base_info_query()
        print_result("基地信息", {
            "现金": base_info.Cash,
            "资源": base_info.Resources,
            "电力": base_info.Power,
            "电力消耗": base_info.PowerDrained,
            "电力供应": base_info.PowerProvided
        })
        
        # 查询屏幕信息
        print("\n🖥️ 查询屏幕信息...")
        screen_info = game_api.screen_info_query()
        print_result("屏幕信息", {
            "屏幕左上角": f"({screen_info.ScreenMin.x}, {screen_info.ScreenMin.y})",
            "屏幕右下角": f"({screen_info.ScreenMax.x}, {screen_info.ScreenMax.y})",
            "鼠标在屏幕上": screen_info.IsMouseOnScreen,
            "鼠标位置": f"({screen_info.MousePosition.x}, {screen_info.MousePosition.y})"
        })
        
    except GameAPIError as e:
        print(f"❌ 查询操作失败: {e.code} - {e.message}")
    except Exception as e:
        print(f"❌ 查询操作异常: {e}")

def test_production_operations(game_api):
    """测试生产操作"""
    print_separator("测试生产操作")
    
    try:
        # 检查是否可以生产步兵
        print("🏭 检查是否可以生产步兵...")
        can_produce = game_api.can_produce("步兵")
        print_result("可以生产步兵", can_produce)
        
        if can_produce:
            # 生产1个步兵
            print("🏭 生产1个步兵...")
            wait_id = game_api.produce("步兵", 1)
            print_result("生产任务ID", wait_id)
            
            if wait_id:
                # 等待生产完成
                print("⏳ 等待生产完成...")
                success = game_api.wait(wait_id, 10.0)
                print_result("生产完成状态", success)
                
                if success:
                    print("✅ 步兵生产完成")
                else:
                    print("⏰ 生产超时")
            else:
                print("❌ 生产任务创建失败")
        else:
            print("❌ 无法生产步兵")
        
        # 查询生产队列
        print("\n📋 查询步兵生产队列...")
        try:
            queue_info = game_api.query_production_queue("Infantry")
            print_result("步兵生产队列", queue_info)
        except Exception as e:
            print(f"❌ 查询生产队列失败: {e}")
        
    except GameAPIError as e:
        print(f"❌ 生产操作失败: {e.code} - {e.message}")
    except Exception as e:
        print(f"❌ 生产操作异常: {e}")

def test_unit_movement(game_api):
    """测试单位移动"""
    print_separator("测试单位移动")
    
    try:
        # 查询自己的单位
        query_param = TargetsQueryParam(faction="自己", type=["步兵"])
        actors = game_api.query_actor(query_param)
        
        if actors:
            print(f"🎯 找到 {len(actors)} 个步兵单位")
            
            # 选择第一个步兵进行移动测试
            test_actor = actors[0]
            print(f"🎯 测试单位: ID={test_actor.actor_id}, 位置=({test_actor.position.x}, {test_actor.position.y})")
            
            # 移动到当前位置附近
            target_location = Location(test_actor.position.x + 5, test_actor.position.y + 5)
            print(f"🎯 移动到目标位置: ({target_location.x}, {target_location.y})")
            
            game_api.move_units_by_location([test_actor], target_location)
            print("✅ 移动命令发送成功")
            
            # 等待移动完成
            print("⏳ 等待移动完成...")
            success = game_api.move_units_by_location_and_wait([test_actor], target_location, max_wait_time=10.0)
            print_result("移动完成状态", success)
            
            if success:
                print("✅ 单位移动完成")
            else:
                print("⏰ 移动超时")
                
        else:
            print("❌ 没有找到可移动的单位")
        
    except GameAPIError as e:
        print(f"❌ 单位移动失败: {e.code} - {e.message}")
    except Exception as e:
        print(f"❌ 单位移动异常: {e}")

def main():
    """主函数"""
    print("🚀 开始真实GameAPI测试")
    print("=" * 60)
    
    # 测试服务器连接
    if not test_server_connection():
        print("❌ 服务器连接失败，测试终止")
        return
    
    # 创建GameAPI实例
    try:
        game_api = GameAPI("localhost", 7445, "zh")
        print("✅ GameAPI实例创建成功")
    except Exception as e:
        print(f"❌ GameAPI实例创建失败: {e}")
        return
    time.sleep(2)
    
    # 执行各种测试
    test_camera_operations(game_api)
    time.sleep(2)
    
    test_building_operations(game_api)
    time.sleep(2)
    
    test_query_operations(game_api)
    time.sleep(2)
    
    test_production_operations(game_api)
    time.sleep(2)
    
    test_unit_movement(game_api)
    time.sleep(2)
    
    print("\n" + "=" * 60)
    print("🎉 所有测试完成！请检查上面的输出结果")
    print("=" * 60)

if __name__ == "__main__":
    main() 