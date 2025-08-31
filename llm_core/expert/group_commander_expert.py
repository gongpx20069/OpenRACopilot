from collections import defaultdict
import time
from typing import List, Optional, Tuple
from OpenRA_Copilot_Library import Actor, Location, TargetsQueryParam
from OpenRA_Copilot_Library.game_api import GameAPI
from .. import BUILDING, VEHICLE, INFANTRIES, AIR

# ================= 配置 =================
SIGHT_RANGE = 10
ATTACK_TICK = 0.6
MAX_TARGET_SECONDS = 1.5
# MAX_TOWER_ASSIGNMENTS = 10
DIST_COEF = 0.15  # 距离分数系数（平方距离）

# 在你的常量区新增一条：明显的非战斗/工具单位（不会主动造成伤害）
NON_COMBAT_TYPES = {"工程师", "间谍", "采矿车", "运输卡车", "基地车"}
DEFENSE_TOWERS = {"火焰塔", "特斯拉塔", "防空导弹"}
COMBAT_UNITS = set(VEHICLE) | set(INFANTRIES) | set(AIR) | DEFENSE_TOWERS

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
        "防空车", "雅克战机", "米格战机", "防空导弹"
    },
    "雌鹿直升机": {
        "防空车", "雅克战机", "米格战机", "防空导弹"
    },
    "黑鹰直升机": {
        "防空车", "雅克战机", "米格战机", "防空导弹"
    },
    "雅克战机": {
        "防空车", "米格战机", "防空导弹"
    },
    "长弓武装直升机": {
        "防空车", "雅克战机", "米格战机", "防空导弹"
    },
    "米格战机": {
        "防空车", "防空导弹"
    },

    # —— 防御建筑 ——
    "火焰塔": {
        "轻坦克", "重型坦克", "超重型坦克", "特斯拉坦克", "震荡坦克", "V2火箭发射车", "长弓武装直升机", "米格战机", "雅克战机"
    },
    "特斯拉塔": {
        "V2火箭发射车", "长弓武装直升机", "米格战机", "超重型坦克", "震荡坦克", "长弓武装直升机", "米格战机", "雅克战机"
    },
    "防空导弹": {
        "轻坦克", "重型坦克", "超重型坦克", "特斯拉坦克", "震荡坦克"
    }
}


class AttackState:
    ATTACK = "attack"
    DEFENSE = "defense"
    RETREAT = "retreat"
    SCOUT = "scout"

# ================= 指挥类 =================
class GroupCommander:
    def __init__(self, api: GameAPI, group_id: int):
        self.api = api
        self.group_id = group_id
        self.current_state = AttackState.DEFENSE
        self.retreat_location: Optional[Location] = None
        self.scout_target: Optional[Location] = None
        self.scout_on_enemy_strategy: Optional[AttackState] = None
        self.active: bool = True

    # ---------------- 工具方法 ----------------
    @staticmethod
    def dist2(a: Location, b: Location) -> float:
        dx = a.x - b.x
        dy = a.y - b.y
        return dx * dx + dy * dy

    @staticmethod
    def center_of(actors: List[Actor]) -> Optional[Location]:
        if not actors:
            return None
        n = len(actors)
        return Location(
            x=sum(a.position.x for a in actors) / n,
            y=sum(a.position.y for a in actors) / n
        )
    
    @staticmethod
    def max_four_direction(actors: List[Actor]) -> List[Location]:
        if not actors:
            return []
        if len(actors) < 6:
            return [actor.position for actor in actors[:3]]

        min_x = max_x = actors[0].position.x
        min_y = max_y = actors[0].position.y
        for a in actors[1:]:
            x = a.position.x
            y = a.position.y
            if x < min_x:
                min_x = x
            if x > max_x:
                max_x = x
            if y < min_y:
                min_y = y
            if y > max_y:
                max_y = y

        mid_x = (min_x + max_x) / 2
        mid_y = (min_x + max_y) / 2
        return [
            Location(x=min_x, y=mid_y),
            Location(x=mid_x, y=min_y),
            Location(x=mid_x, y=max_y),
            Location(x=max_x, y=mid_y)
        ]

    def get_group_actors(self) -> List[Actor]:
        # 按你最初的写法：使用“己方”+ group_id 查询
        return self.api.query_actor(TargetsQueryParam(group_id=[self.group_id], faction="己方"))

    def get_visible_enemies(self) -> List[Actor]:
        return self.api.query_actor(TargetsQueryParam(faction="敌方", restrain=[{"visible": True}]))

    def get_base_position(self) -> Optional[Location]:
        # 优先找“建造厂”，否则取我方任意建筑中心
        bases = self.api.query_actor(TargetsQueryParam(type=["建造厂"], faction="己方"))
        if bases:
            return bases[0].position

        my_buildings = self.api.query_actor(TargetsQueryParam(type=list(BUILDING), faction="己方"))
        if my_buildings:
            return self.center_of(my_buildings)
        return None

    def filter_nearby(self, actors: List[Actor], center: List[Location]) -> List[Actor]:
        if not actors:
            return []
        sr2 = SIGHT_RANGE * SIGHT_RANGE
        d2 = self.dist2
        return [a for a in actors if any(d2(a.position, c) <= sr2 for c in center)]

    def has_air(self, actors: List[Actor]) -> bool:
        return any(a.type in AIR for a in actors)

    # ---------------- 优先级计算（防御模式） ----------------
    def _categorize_enemies_defense(self, enemies: List[Actor], my_has_air: bool) -> Tuple[List[Actor], List[Actor], List[Actor], List[Actor]]:
        """返回 (towers, combats, non_combat, buildings) 四类，分类只做一次"""
        towers, combats, non_combat, buildings = [], [], [], []
        for e in enemies:
            et = e.type
            if et in {"火焰塔", "特斯拉塔"}:
                towers.append(e)
            elif et == "防空导弹":
                if my_has_air:
                    towers.append(e)
                else:
                    buildings.append(e)
            elif et in NON_COMBAT_TYPES:
                non_combat.append(e)
            elif et in COMBAT_UNITS:
                combats.append(e)
            elif et in BUILDING:
                buildings.append(e)
            else:
                # 未知类型：保守按作战单位处理（更安全）
                combats.append(e)
        return towers, combats, non_combat, buildings

    def _score_pair_defense(self, me: Actor, enemy: Actor, prio: int) -> float:
        """给定我方actor与目标，根据优先级返回综合分。距离只在 prio 1/2 生效。"""
        # 基础分
        if prio == 1:
            base = 150
        elif prio == 2:
            base = 80
        elif prio == 3:
            base = 40
        else:
            base = 10

        # 克制关系
        ctr = 0
        myt = me.type
        et = enemy.type
        if et in COUNTERED_BY.get(myt, ()):
            ctr += 20
        if myt in COUNTERED_BY.get(et, ()):
            ctr -= 10

        # 距离分（只对 1/2）
        if prio <= 2:
            d2 = self.dist2(me.position, enemy.position)
            return base + ctr - d2 * DIST_COEF
        return base + ctr

    def assign_targets_defense(self, my_actors: List[Actor], enemies: List[Actor]) -> List[Tuple[Actor, Actor]]:
        """
        防御模式目标分配（优化版）：
        1. 防御塔（火焰塔/特斯拉塔 + 若有空军则包含防空导弹）
        - 对塔有克制作用的单位，平均分配到不同塔
        - 其他单位也尽量均匀分配
        2. 敌方作战单位
        3. 敌方非战斗单位
        4. 建筑（含无空军时的防空导弹）
        """
        if not my_actors or not enemies:
            return []

        assignments: List[Tuple[Actor, Actor]] = []
        my_has_air = self.has_air(my_actors)

        # 一次性分类敌人
        towers, combats, non_combat, buildings = self._categorize_enemies_defense(enemies, my_has_air)
        priority_groups = ((2, combats), (3, non_combat), (4, buildings))  # 1级塔单独处理

        score_pair = self._score_pair_defense

        # ---------- Step 1: 塔的均匀分配 ----------
        assigned_ids = set()
        if towers:
            tower_list = list(towers)
            n_towers = len(tower_list)

            # 预先缓存：我方单位是否克制塔
            def is_counter_unit(me: Actor) -> bool:
                return any(t.type in COUNTERED_BY.get(me.type, ()) for t in tower_list)

            counter_units = [me for me in my_actors if is_counter_unit(me)]
            normal_units = [me for me in my_actors if me not in counter_units]

            # 克制单位均分
            for i, me in enumerate(counter_units):
                tower = tower_list[i % n_towers]
                assignments.append((me, tower))
                assigned_ids.add(me.actor_id)

            # 其他单位均分
            for i, me in enumerate(normal_units):
                tower = tower_list[i % n_towers]
                assignments.append((me, tower))
                assigned_ids.add(me.actor_id)

        # ---------- Step 2: 其他优先级目标 ----------
        for me in my_actors:
            if me.actor_id in assigned_ids:
                continue  # 已分配过（对塔）

            best_enemy, best_score = None, float("-inf")

            for prio, group in priority_groups:
                if not group:
                    continue
                for enemy in group:
                    s = score_pair(me, enemy, prio)
                    if s > best_score:
                        best_score, best_enemy = s, enemy

            if best_enemy:
                assignments.append((me, best_enemy))

        return assignments

    # ---------------- 执行方法 ----------------
    def attack_target_until_done(self, targets: List[Actor], assigner) -> str:
        """
        循环在限定时间内持续分配并下达 attack 命令。
        targets 列表会就地剔除已死亡/超出范围的目标。
        """
        t0 = time.monotonic()
        update_actor = self.api.update_actor
        attack_target = self.api.attack_target
        dist2 = self.dist2
        sr2 = SIGHT_RANGE * SIGHT_RANGE

        while time.monotonic() - t0 < MAX_TARGET_SECONDS and targets:
            # 刷新我方
            my_now = self.get_group_actors()
            if not my_now:
                self.active = False
                return "no_me"

            # 清理目标：死亡
            targets[:] = [t for t in targets if update_actor(t)]
            if not targets:
                return "ok"

            # 视野检查：若所有目标都超出范围，结束本轮
            four_directions = GroupCommander.max_four_direction(my_now)
            if (not four_directions) or all(dist2(t.position, c) > sr2 for c in four_directions for t in targets):
                return "ok"

            # 分配与下达攻击
            for attacker, target in assigner(my_now, targets):
                attack_target(attacker=attacker, target=target)

            time.sleep(ATTACK_TICK)

        return "timeout"

    # ========== 状态逻辑 ==========
    def execute_defense(self):
        """防御模式：持续在视野内清理‘非建筑’为主（塔/战斗/非战斗），建筑最低优先。"""
        my_actors = self.get_group_actors()
        if not my_actors:
            self.active = False
            return

        four_directions = self.max_four_direction(my_actors)
        if not four_directions:
            self.active = False
            return

        enemies = self.get_visible_enemies()
        nearby = self.filter_nearby(enemies, four_directions)
        if not nearby:
            # 视野内无敌方，结束本轮
            self.active = False
            return

        # 只用“防御分配器”
        self.attack_target_until_done(nearby, assigner=self.assign_targets_defense)

    def execute_attack(self):
        """进攻模式（可按需要扩展你自己的进攻优先级）"""
        my_actors = self.get_group_actors()
        if not my_actors:
            self.active = False
            return

        four_directions = self.max_four_direction(my_actors)
        if not four_directions:
            self.active = False
            return

        enemies = self.get_visible_enemies()
        nearby = self.filter_nearby(enemies, four_directions)
        if not nearby:
            self.active = False
            return

        # 进攻这里也可直接复用防御分配（简单可靠），或替换为你的进攻策略
        self.attack_target_until_done(nearby, assigner=self.assign_targets_defense)


    def execute_retreat(self):
        """撤退：若提供 retreat_location 则优先使用；否则自动回基地（建造厂或我方建筑中心）"""
        my_actors = self.get_group_actors()
        if not my_actors:
            self.active = False
            return

        # 目标位置：用户给的 > 基地 > 直接返回
        dest = self.retreat_location or self.get_base_position()
        if not dest:
            self.active = False
            return

        # 非攻击性移动
        self.api.move_units_by_location(my_actors, dest, attack_move=False)
        self.active = False

    # ---------------- 探路 -----------------
    def group_by_armor(self, actors: List[Actor]) -> List[List[Actor]]:
        heavy_types = {"重型坦克", "超重型坦克", "特斯拉坦克", "震荡坦克"}
        air = [a for a in actors if a.type in AIR]
        heavy = [a for a in actors if a.type in heavy_types]
        light_vehicles = [a for a in actors if a.type in VEHICLE and a.type not in NON_COMBAT_TYPES and a.type not in heavy_types]
        infantry = [a for a in actors if a.type in INFANTRIES and a.type not in NON_COMBAT_TYPES]

        groups = [air, heavy, light_vehicles, infantry]
        return [g for g in groups if g]
    
    @staticmethod
    def generate_path(start: Location, end: Location, step: float) -> List[Location]:
        dx = end.x - start.x
        dy = end.y - start.y
        dist = (dx ** 2 + dy ** 2) ** 0.5
        if dist == 0:
            return [start]
        ux = dx / dist
        uy = dy / dist
        path = [start]
        current = step
        while current < dist:
            path.append(Location(x=start.x + ux * current, y=start.y + uy * current))
            current += step
        path.append(end)
        return path
    
    
    def execute_scout(self):
        """探路模式：分组单位，按顺序逐点移动，保持距离，遇到敌人切换状态。"""
        if not self.scout_target:
            self.active = False
            return
        
        my_actors = self.get_group_actors()
        if not my_actors:
            self.active = False
            return
        
        groups = self.group_by_armor(my_actors)
        if not groups:
            self.active = False
            return
        
        start = self.center_of(my_actors)
        if not start:
            self.active = False
            return
        
        # 使用10格步长以匹配距离保持
        path = self.generate_path(start, self.scout_target, step=5)
        if len(path) < 2:
            self.active = False
            return
        
        current_idx = 1  # 从第一个中间点开始
        last_idx = 0
        t0 = time.monotonic()
        arrival_dist2 = 2**2  # 2^2

        while current_idx < len(path):
            # 更新actor状态
            for group in groups:
                for actor in group:
                    self.api.update_actor(actor=actor)
            
            lead_center = self.center_of(groups[0])
            enemies = self.get_visible_enemies()
            nearby = self.filter_nearby(enemies, [lead_center])
            if nearby:
                # 切换状态
                if self.scout_on_enemy_strategy in (AttackState.ATTACK, AttackState.DEFENSE, AttackState.RETREAT):
                    self.current_state = self.scout_on_enemy_strategy
                
                self.active = True
                return  # 退出探路，下一run执行新状态
            
            # 检查探路先锋是否到达当前目标
            lead_target = path[current_idx]
            if self.dist2(lead_center, lead_target) < arrival_dist2 or time.monotonic() - t0 > 5:
                current_idx += 1
                t0 = time.monotonic()
                if current_idx >= len(path):
                    # 将所有单位都移动到end
                    for g_idx, group in enumerate(groups):
                        self.api.move_units_by_location(group, path[-2], attack_move=False)
                    self.active = False
                    return
                
            if current_idx > last_idx:
                # 计算各组目标点（保持5格距离，通过索引偏移）
                group_targets = []
                for i in range(len(groups)):
                    idx = max(0, current_idx - i)
                    group_targets.append(path[idx])

                # 下达移动命令
                for g_idx, group in enumerate(groups):
                    self.api.move_units_by_location(group, group_targets[g_idx], attack_move=False)
                    
                last_idx = current_idx

            time.sleep(ATTACK_TICK)


    # ---------------- 主入口 ----------------
    def set_state(self, state: str, scout_on_enemy_strategy:str = AttackState.DEFENSE, retreat_location: Optional[Location] = None, scout_location: Optional[Location] = None):
        if state not in (AttackState.ATTACK, AttackState.DEFENSE, AttackState.RETREAT, AttackState.SCOUT):
            raise ValueError("Invalid state")
        if scout_on_enemy_strategy not in (AttackState.ATTACK, AttackState.DEFENSE, AttackState.RETREAT):
            raise ValueError("Invalid on_enemy_strategy")
        self.current_state = state
        self.scout_on_enemy_strategy = scout_on_enemy_strategy

        self.retreat_location = retreat_location
        self.scout_target = scout_location

    def run(self):
        if not self.active:
            self.active = True  # 允许外部先设state后直接run
        if self.current_state == AttackState.ATTACK:
            self.execute_attack()
        elif self.current_state == AttackState.DEFENSE:
            self.execute_defense()
        elif self.current_state == AttackState.RETREAT:
            self.execute_retreat()
        elif self.current_state == AttackState.SCOUT:
            self.execute_scout()