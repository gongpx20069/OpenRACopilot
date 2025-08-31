import logging
import sys
import os

logger = logging.getLogger("AgentSystem")

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from llm_core.expert.task_classifier_expert import AgentCategory, task_classifier_function


def run_tests():
    """运行简化的函数式测试，验证 task_classifier_function 的功能。"""
    test_cases = [
        # 测试 build_agent
        ("请建造一个新维修厂", "building_agent"),
        ("生产10个重坦克", "building_agent"),
        ("修复所有受损建筑", "building_agent"),
        ("修复受损坦克", "building_agent"),
        ("生产10个士兵", "building_agent"),
        
        # 测试 squad_leader_agent
        ("小队1攻击敌人", "squad_commander_agent"),
        ("队2移动到坐标", "squad_commander_agent"),
        ("小队1防御阵地", "squad_commander_agent"),
        ("小队2移动到建造厂位置", "squad_commander_agent"),
        ("小队2移动到维修厂位置", "squad_commander_agent"),
        
        # 测试 formation_agent
        ("将所有防空车编队为队1", "squad_formation_agent"),
        ("将所有坦克和维修厂编队为队2", "squad_formation_agent"),
        
        # 测试 other_agent
        ("移动防空车到地图左上角", "default_executer_agent"),
        ("移动防空车到建造厂位置", "default_executer_agent")
    ]

    AGENT_MAP = {
        AgentCategory.BUILD: "building_agent",
        AgentCategory.FORMATION: "squad_formation_agent",
        AgentCategory.SQUAD_LEADER: "squad_commander_agent",
        AgentCategory.OTHER: "default_executer_agent",
    }
    
    passed = 0
    total = len(test_cases)
    
    for query, expected in test_cases:
        result = task_classifier_function(query, AGENT_MAP)
        if result == expected:
            print(f"PASS: Query '{query}' -> Agent: {result}")
            passed += 1
        else:
            print(f"FAIL: Query '{query}' -> Expected: {expected}, Got: {result}")
    
    print(f"\nTest Summary: {passed}/{total} tests passed")
    if passed == total:
        print("All tests passed!")
    else:
        print("Some tests failed.")

if __name__ == "__main__":
    run_tests()