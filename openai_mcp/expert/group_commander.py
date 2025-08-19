import time
from typing import List, Optional
from OpenRA_Copilot_Library import Actor, Location, TargetsQueryParam
from OpenRA_Copilot_Library.game_api import GameAPI
from ..mcp_server import BUILDING, VEHICLE, INFANTRIES, AIR

# ================= 配置 =================
SIGHT_RANGE = 11
ATTACK_TICK = 0.6
MAX_TARGET_SECONDS = 1.5

# 在你的常量区新增一条：明显的非战斗/工具单位（不会主动造成伤害）
NON_COMBAT_TYPES = {"工程师", "间谍", "采矿车", "运输卡车", "基地车"}
DEFENSE_TOWERS = ["火焰塔", "特斯拉塔", "防空导弹"]

COUNTERED_BY = {
    # —— 步兵类 ——
    "步兵": {
        "军犬", "吉普车", "轻坦克", "重型坦克", "超重型坦克",
        "喷火兵", "掷弹兵", "V2火箭发射车", "雌鹿直升机",
        "长弓武装直升机", "雅克战机", "防空车"
    },
    "火箭兵": {
        "军犬", "吉普车", "装甲运输车", "轻坦克", "重型坦克", "超重型坦克",
        "喷火兵", "掷弹兵", "雌鹿直升机", "长弓武装直升机", "雅克战机",
        "防空车"
    },
    "工程师": {
        "军犬", "步兵", "吉普车", "轻坦克", "重型坦克", "超重型坦克",
        "雌鹿直升机", "长弓武装直升机", "雅克战机", "米格战机"
    },
    "掷弹兵": {
        "军犬", "吉普车", "轻坦克", "重型坦克", "超重型坦克",
        "雌鹿直升机", "长弓武装直升机", "雅克战机", "防空车"
    },
    "军犬": {
        "步兵", "掷弹兵", "喷火兵", "吉普车", "轻坦克",
        "雌鹿直升机", "长弓武装直升机", "雅克战机"
    },
    "喷火兵": {
        "吉普车", "轻坦克", "重型坦克", "超重型坦克",
        "雌鹿直升机", "长弓武装直升机", "雅克战机"
    },
    "间谍": {
        "军犬", "步兵"
    },
    "磁暴步兵": {
        "军犬", "吉普车", "装甲运输车", "雌鹿直升机",
        "长弓武装直升机", "雅克战机", "米格战机", "V2火箭发射车"
    },

    # —— 载具类 ——
    "采矿车": {
        "火箭兵", "轻坦克", "重型坦克", "超重型坦克",
        "长弓武装直升机", "米格战机"
    },
    "装甲运输车": {
        "火箭兵", "轻坦克", "重型坦克", "超重型坦克",
        "长弓武装直升机", "米格战机"
    },
    "防空车": {
        # 修正：不再被 “火箭兵 / V2火箭发射车 / 空军” 标为克制
        "轻坦克", "重型坦克", "超重型坦克", "特斯拉坦克", "震荡坦克", "装甲运输车"
    },
    "基地车": {
        "火箭兵", "重型坦克", "超重型坦克", "长弓武装直升机", "米格战机"
    },
    "轻坦克": {
        "火箭兵", "重型坦克", "超重型坦克", "特斯拉坦克", "震荡坦克",
        "长弓武装直升机", "米格战机", "V2火箭发射车", "磁暴步兵"
    },
    "吉普车": {
        "火箭兵", "轻坦克", "重型坦克", "长弓武装直升机", "米格战机"
    },
    "重型坦克": {
        "火箭兵", "超重型坦克", "特斯拉坦克", "震荡坦克",
        "长弓武装直升机", "米格战机", "V2火箭发射车", "磁暴步兵"
    },
    "V2火箭发射车": {
        # 调整：去掉“火箭兵”克制；它主要怕机动近扑与空军
        "吉普车", "轻坦克", "重型坦克",
        "雌鹿直升机", "长弓武装直升机", "雅克战机", "米格战机"
    },
    "地雷部署车": {
        "轻坦克", "重型坦克", "超重型坦克"
    },
    "超重型坦克": {
        "火箭兵", "特斯拉坦克", "震荡坦克",
        "长弓武装直升机", "米格战机", "V2火箭发射车"
    },
    "特斯拉坦克": {
        "火箭兵", "长弓武装直升机", "米格战机", "重型坦克", "超重型坦克"
    },
    "震荡坦克": {
        "火箭兵", "长弓武装直升机", "米格战机", "雅克战机"
    },
    "运输卡车": {
        "吉普车", "轻坦克", "重型坦克", "长弓武装直升机", "米格战机"
    },

    # —— 空军类 ——
    "运输直升机": {
        "防空车", "雅克战机", "米格战机"
    },
    "雌鹿直升机": {
        "防空车", "雅克战机", "米格战机"
    },
    "黑鹰直升机": {
        "防空车", "雅克战机", "米格战机"
    },
    "雅克战机": {
        "防空车", "米格战机"
    },
    "长弓武装直升机": {
        "防空车", "雅克战机", "米格战机"
    },
    "米格战机": {
        "防空车", "雅克战机"
    }
}


class AttackState:
    ATTACK = "attack"
    DEFENSE = "defense"
    RETREAT = "retreat"

class GroupCommander:
    def __init__(self, api: GameAPI, group_id: int):
        self.api = api
        self.group_id = group_id
        self.current_state = AttackState.DEFENSE
        self.retreat_location: Optional[Location] = None
        self.active: bool = True

    # ---------------- 基础查询 ----------------
    def get_group_actors(self) -> List[Actor]:
        query = TargetsQueryParam(group_id=[self.group_id], faction="己方")
        return self.api.query_actor(query)

    def get_all_visible_enemies_once(self) -> List[Actor]:
        query = TargetsQueryParam(faction="敌方", restrain=[{"visible": True}])
        return self.api.query_actor(query)

    def get_own_base_position(self) -> Optional[Location]:
        bases = self.api.query_actor(TargetsQueryParam(type=["建造厂"], faction="己方"))
        return bases[0].position if bases else None

    # ---------------- 工具方法 ----------------
    @staticmethod
    def distance(a: Location, b: Location) -> float:
        dx, dy = a.x - b.x, a.y - b.y
        return (dx*dx + dy*dy) ** 0.5

    @staticmethod
    def center_of(actors: List[Actor]) -> Optional[Location]:
        if not actors: return None
        sx = sum(a.position.x for a in actors)
        sy = sum(a.position.y for a in actors)
        return Location(x=sx/len(actors), y=sy/len(actors))

    def filter_nearby(self, actors: List[Actor], group_center: Location) -> List[Actor]:
        return [e for e in actors if self.distance(e.position, group_center) <= SIGHT_RANGE]

    def has_air(self, group_actors: List[Actor]) -> bool:
        return any(a.type in AIR for a in group_actors)

    def sort_enemies_by_counter(self, enemies: List[Actor], my_actors: List[Actor]) -> List[Actor]:
        """根据克制关系给敌方排序：克制我方的威胁高，反之威胁低。"""
        def score(enemy: Actor) -> int:
            s = 0
            for me in my_actors:
                if enemy.type in COUNTERED_BY.get(me.type, []):
                    s += 1
                if me.type in COUNTERED_BY.get(enemy.type, []):
                    s -= 1
            return s
        return sorted(enemies, key=score, reverse=True)

    def get_priority_level(self, enemy: Actor, has_air: bool) -> int:
        """敌人优先级：塔 → 战斗单位 → 非战斗单位 → 建筑"""
        if enemy.type in ("火焰塔", "特斯拉塔"):
            return 1
        if has_air and enemy.type == "防空导弹":
            return 1
        if enemy.type in INFANTRIES or enemy.type in VEHICLE or enemy.type in AIR:
            return 2
        if enemy.type in NON_COMBAT_TYPES:
            return 3
        if enemy.type in BUILDING:
            return 4 if not (has_air and enemy.type == "防空导弹") else 1
        return 4

    def prioritize_targets(self, enemies: List[Actor], group_actors: List[Actor], attack_buildings: bool = True) -> List[Actor]:
        has_air = self.has_air(group_actors)
        level_map = {1: [], 2: [], 3: [], 4: []}
        for e in enemies:
            lvl = self.get_priority_level(e, has_air)
            if lvl == 4 and not attack_buildings:
                continue
            level_map[lvl].append(e)

        level_map[2] = self.sort_enemies_by_counter(level_map[2], group_actors)
        return level_map[1] + level_map[2] + level_map[3] + level_map[4]

    # ---------------- 新增：单位分配目标 ----------------
    def assign_targets(self, my_actors: List[Actor], enemies: List[Actor]) -> List[tuple]:
        prioritized_enemies = self.prioritize_targets(enemies, my_actors)
        assignments = []
        remaining_enemies = prioritized_enemies[:]  # Use prioritized list for fallback
        for me in my_actors:
            best_target = None
            # First, look for a target that this unit counters (me counters enemy)
            for enemy in remaining_enemies:
                if me.type in COUNTERED_BY.get(enemy.type, []):
                    best_target = enemy
                    break
            # If no countered target found, fallback to the highest priority remaining
            if not best_target and remaining_enemies:
                best_target = remaining_enemies[0]
            if best_target:
                assignments.append((me, best_target))
                # Remove to avoid over-assignment, but allow multiples if needed later
                remaining_enemies.remove(best_target)
        return assignments

    # ---------------- 攻击核心 ----------------
    def attack_target_until_done(self, targets: List[Actor], my_actors: List[Actor], group_center: Location) -> str:
        t0 = time.monotonic()
        while time.monotonic() - t0 < MAX_TARGET_SECONDS:
            my = self.get_group_actors()
            if not my:
                self.active = False
                return "no_me"

            for t in targets[:]:
                if not self.api.update_actor(t) or getattr(t, "hppercent", 0) <= 0:
                    targets.remove(t)

            if not targets:
                return "ok"

            my_center = self.center_of(my)
            if not my_center:
                self.active = False
                return "no_me"
            if all(self.distance(t.position, my_center) > SIGHT_RANGE for t in targets):
                return "ok"

            assignments = self.assign_targets(my, targets)
            for attacker, target in assignments:
                self.api.attack_target(attacker=attacker, target=target)

            time.sleep(ATTACK_TICK)

        return "timeout"

    # ---------------- 行为逻辑 ----------------
    def execute_attack(self):
        while self.active:
            my_actors = self.get_group_actors()
            if not my_actors:
                self.active = False
                break
            my_center = self.center_of(my_actors)
            if not my_center:
                self.active = False
                break

            enemies = self.get_all_visible_enemies_once()
            nearby = self.filter_nearby(enemies, my_center)
            if not nearby:
                self.active = False
                break

            targets = self.prioritize_targets(nearby, my_actors, attack_buildings=True)
            self.attack_target_until_done(targets, my_actors, my_center)
            time.sleep(ATTACK_TICK)

    def execute_defense(self):
        while self.active:
            my_actors = self.get_group_actors()
            if not my_actors:
                self.active = False
                break
            my_center = self.center_of(my_actors)
            if not my_center:
                self.active = False
                break

            enemies = self.get_all_visible_enemies_once()
            nearby = self.filter_nearby(enemies, my_center)
            nearby_combat = [e for e in nearby if e.type not in BUILDING]
            if not nearby_combat:
                self.active = False
                break

            targets = self.prioritize_targets(nearby_combat, my_actors, attack_buildings=False)
            self.attack_target_until_done(targets, my_actors, my_center)
            time.sleep(ATTACK_TICK)

    def execute_retreat(self):
        my_actors = self.get_group_actors()
        if not my_actors:
            self.active = False
            return
        location = self.retreat_location or self.get_own_base_position()
        if not location:
            self.active = False
            return
        self.api.move_units_by_location(my_actors, location, attack_move=False)
        self.active = False

    # ---------------- 主入口 ----------------
    def set_state(self, state: str, retreat_location: Optional[Location] = None):
        if state not in (AttackState.ATTACK, AttackState.DEFENSE, AttackState.RETREAT):
            raise ValueError("Invalid state")
        self.current_state = state
        self.retreat_location = retreat_location if state == AttackState.RETREAT else None

    def run(self):
        if not self.active:
            return
        if self.current_state == AttackState.ATTACK:
            self.execute_attack()
        elif self.current_state == AttackState.DEFENSE:
            self.execute_defense()
        elif self.current_state == AttackState.RETREAT:
            self.execute_retreat()