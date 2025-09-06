from enum import Enum
import re
from typing import Dict
from agents import Agent


# 定义类别枚举，提高类型安全
class AgentCategory:
    BUILD = "build_agent"
    FORMATION = "formation_agent"
    SQUAD_LEADER = "squad_leader_agent"
    OTHER = "other_agent"
    TASK_CLASSIFIER = "task_classifier_agent"


def __compile_keyword_patterns() -> Dict[str, re.Pattern]:
    patterns = {}

    # === 建造/生产类 ===
    build_keywords = ["建造", "生产", "放置", "修复", "维修"]
    build_pattern = r"(" + "|".join(map(re.escape, build_keywords)) + r")[\s\d\u4e00-\u9fff]+"
    patterns[AgentCategory.BUILD] = re.compile(build_pattern, re.UNICODE)

    # === 编队类（不需要前缀） ===
    # 注意：这里包含正则表达式，不需要 re.escape
    formation_keywords = [r"编队", r"组队", r"将.*编队", r"将.*移除", r"将.*加入", r"将.*移出", r"从队伍.*移除", r"从队伍.*移出"]
    formation_pattern = "(" + "|".join(formation_keywords) + ")"
    patterns[AgentCategory.FORMATION] = re.compile(formation_pattern, re.UNICODE)


    # === 小队作战类（必须有前缀） ===
    squad_leader_keywords = ["移动", "攻击", "防御", "撤退", "探路", "探索"]
    squad_leader_pattern = (
        r'^(?:小队|队|编队|将队|将小队|将编队).*(?:' + "|".join(map(re.escape, squad_leader_keywords)) + ")"
    )
    patterns[AgentCategory.SQUAD_LEADER] = re.compile(squad_leader_pattern, re.UNICODE)

    return patterns


KEYWORD_PATTERNS = __compile_keyword_patterns()


# ================== 分类函数 ==================
def task_classifier_function(query: str, agent_map: Dict[str, Agent]) -> Agent:
    if not query:
        return agent_map[AgentCategory.OTHER]

    # 内置专有建筑列表
    PROPER_BUILDINGS = ("建造厂", "维修厂", "建造场", "维修场")

    # 1. 小队作战类
    squad_pattern = KEYWORD_PATTERNS.get(AgentCategory.SQUAD_LEADER)
    if squad_pattern and squad_pattern.search(query):
        return agent_map[AgentCategory.SQUAD_LEADER]

    # 2. 编队类
    formation_pattern = KEYWORD_PATTERNS.get(AgentCategory.FORMATION)
    if formation_pattern and formation_pattern.search(query):
        return agent_map[AgentCategory.FORMATION]

    # 3. 建造/生产类（先排除专有建筑名干扰）
    for key in PROPER_BUILDINGS:
        query = query.replace(key, "")
    build_pattern = KEYWORD_PATTERNS.get(AgentCategory.BUILD)
    if build_pattern and build_pattern.search(query):
        return agent_map[AgentCategory.BUILD]

    # 4. 其他
    return agent_map[AgentCategory.OTHER]