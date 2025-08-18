import time
from typing import List, Optional
from OpenRA_Copilot_Library import Actor, Location, TargetsQueryParam
from OpenRA_Copilot_Library.game_api import GameAPI
from ..mcp_server import BUILDING, VEHICLE, INFANTRIES, AIR

# ================= 配置 =================
SIGHT_RANGE = 15
ATTACK_TICK = 0.6
MAX_TARGET_SECONDS = 10.0

DEFENSE_TOWERS = ["火焰塔", "特斯拉塔", "防空导弹"]
HIGH_THREAT_UNITS = ["军犬", "火箭兵", "防空车", "特斯拉坦克", "震荡坦克"]

COUNTER_RELATIONS = {
    "步兵": ["军犬"],
    "火箭兵": ["轻坦克", "重型坦克", "超重型坦克"] + AIR,
    "掷弹兵": ["步兵", "建筑"],
    "军犬": ["步兵", "间谍", "工程师"],
    "轻坦克": ["步兵", "掷弹兵", "喷火兵"],
    "重型坦克": ["步兵", "掷弹兵", "喷火兵"],
    "超重型坦克": ["步兵", "掷弹兵", "喷火兵"],
    "防空车": AIR,
    "V2火箭发射车": ["建筑", "步兵"],
    "特斯拉坦克": ["重型坦克", "超重型坦克"],
    "震荡坦克": ["重型坦克", "超重型坦克", "建筑"],
    "黑鹰直升机": ["建筑", "步兵"],
    "雅克战机": ["建筑", "步兵", "载具"],
    "长弓武装直升机": ["载具", "建筑"],
    "米格战机": ["载具", "建筑"],
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
        bases = self.api.query_actor(TargetsQueryParam(type=["建造厂"], faction="自己"))
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
        def score(enemy: Actor) -> int:
            s = 0
            for me in my_actors:
                if enemy.type in COUNTER_RELATIONS.get(me.type, []): s -= 1
                if me.type in COUNTER_RELATIONS.get(enemy.type, []): s += 1
            return s
        return sorted(enemies, key=score, reverse=True)

    def prioritize_targets(self, enemies: List[Actor], group_actors: List[Actor], attack_buildings: bool = True) -> List[Actor]:
        has_air = self.has_air(group_actors)
        defense_towers = DEFENSE_TOWERS if has_air else ["火焰塔", "特斯拉塔"]
        towers = [e for e in enemies if e.type in defense_towers]
        high_threats = [e for e in enemies if e.type in HIGH_THREAT_UNITS]
        rest_units = [e for e in enemies if (e not in towers and e not in high_threats and e.type not in BUILDING)]
        rest_sorted = self.sort_enemies_by_counter(rest_units, group_actors)
        buildings = [e for e in enemies if (e.type in BUILDING and e not in towers)] if attack_buildings else []
        return towers + high_threats + rest_sorted + buildings

    # ---------------- 攻击核心 ----------------
    def attack_target_until_done(self, target: Actor, group_center: Location) -> str:
        t0 = time.monotonic()
        while time.monotonic() - t0 < MAX_TARGET_SECONDS:
            my = self.get_group_actors()
            if not my:
                self.active = False
                return "no_me"

            if not self.api.update_actor(target) or getattr(target, "hppercent", 0) <= 0:
                return "skip"

            my_center = self.center_of(my)
            if not my_center:
                self.active = False
                return "no_me"
            if self.distance(target.position, my_center) > SIGHT_RANGE:
                return "ok"

            attacker_ids = [a.actor_id for a in my]
            if not attacker_ids:
                self.active = False
                return "no_me"

            for attacker in attacker_ids:
                self.api.attack_target(attacker=Actor(actor_id=attacker), target=target)
            time.sleep(ATTACK_TICK)

            if not self.api.update_actor(target) or getattr(target, "hppercent", 0) <= 0:
                return "ok"
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
            for tgt in targets:
                if not self.active:
                    break
                result = self.attack_target_until_done(tgt, my_center)
                if result == "no_me":
                    break

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
            for tgt in targets:
                if not self.active:
                    break
                result = self.attack_target_until_done(tgt, my_center)
                if result == "no_me":
                    break

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
