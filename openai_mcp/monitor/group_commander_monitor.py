import threading
import time
from typing import Dict, List, Optional

# 你已有的依赖
from OpenRA_Copilot_Library import Actor, Location
from OpenRA_Copilot_Library.game_api import GameAPI
from ..expert.group_commander import GroupCommander, AttackState  # 按你项目里的路径

# =================== CommanderWorker ===================
class CommanderWorker(threading.Thread):
    """
    循环驱动一个 GroupCommander，维护当前参战我方 actors 的快照，供 Monitor/外部线程查询。
    """
    def __init__(self, commander: GroupCommander, tick: float = 0.3):
        super().__init__(daemon=True)
        self.commander = commander
        self.tick = tick
        self._stop_flag = threading.Event()
        self._snapshot_lock = threading.RLock()
        self._participants_snapshot: List[Actor] = []
        self._last_snapshot_ts: float = 0.0

    def run(self):
        try:
            while not self._stop_flag.is_set() and self.commander.active:
                self.commander.run()

                # 刷新参战我方快照
                try:
                    participants = self.commander.get_group_actors()
                except Exception:
                    participants = []

                with self._snapshot_lock:
                    self._participants_snapshot = participants
                    self._last_snapshot_ts = time.monotonic()

                time.sleep(self.tick)
        finally:
            # 退出前清空快照
            with self._snapshot_lock:
                self._participants_snapshot = []

    def stop(self):
        self._stop_flag.set()
        self.commander.active = False

    def get_participants_snapshot(self) -> List[Actor]:
        with self._snapshot_lock:
            return list(self._participants_snapshot)

    def last_snapshot_time(self) -> float:
        with self._snapshot_lock:
            return self._last_snapshot_ts


# =================== GroupMonitor (单例) ===================
class GroupMonitor(threading.Thread):
    """
    全局唯一 GroupMonitor：
    - 管理多个 GroupCommander
    - 提供查询接口
    """
    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, api: GameAPI, tick: float = 0.3):
        if hasattr(self, "_initialized") and self._initialized:
            return
        super().__init__(daemon=True)
        self._initialized = True

        self.api = api
        self.tick = tick
        self._running = threading.Event()
        self._running.set()

        self._lock = threading.RLock()
        self._commanders: Dict[int, GroupCommander] = {}
        self._workers: Dict[int, CommanderWorker] = {}

    # ---------- 生命周期 ----------
    def run(self):
        while self._running.is_set():
            with self._lock:
                # 回收已结束 commander
                to_remove = [gid for gid, cmd in self._commanders.items() if not cmd.active]
                for gid in to_remove:
                    worker = self._workers.pop(gid, None)
                    if worker:
                        worker.stop()
                    self._commanders.pop(gid, None)
            time.sleep(self.tick)

    def stop(self):
        self._running.clear()
        with self._lock:
            for worker in self._workers.values():
                worker.stop()
        for worker in list(self._workers.values()):
            worker.join(timeout=1.0)

    # ---------- 管理 GroupCommander ----------
    def start_group(self, group_id: int, state: str, retreat_location: Optional[Location] = None) -> bool:
        """
        启动一个 group 的战斗线程
        返回 False 表示该 group_id 已存在且仍在运行
        """
        with self._lock:
            if group_id in self._commanders and self._commanders[group_id].active:
                return False

            commander = GroupCommander(self.api, group_id)
            commander.set_state(state, retreat_location=retreat_location)

            worker = CommanderWorker(commander, tick=self.tick)
            self._commanders[group_id] = commander
            self._workers[group_id] = worker
            worker.start()
            return True

    def stop_group(self, group_id: int) -> None:
        with self._lock:
            cmd = self._commanders.get(group_id)
            if cmd:
                cmd.active = False
            worker = self._workers.get(group_id)
            if worker:
                worker.stop()

    def list_groups(self) -> List[int]:
        with self._lock:
            return list(self._commanders.keys())

    # ---------- 查询接口 ----------
    def is_group_registered(self, group_id: int) -> bool:
        with self._lock:
            return group_id in self._commanders

    def is_group_running(self, group_id: int) -> bool:
        with self._lock:
            cmd = self._commanders.get(group_id)
            return bool(cmd and cmd.active)

    def is_group_fighting(self, group_id: int) -> bool:
        with self._lock:
            cmd = self._commanders.get(group_id)
            if not cmd or not cmd.active:
                return False
            return cmd.current_state in (AttackState.ATTACK, AttackState.DEFENSE)

    def get_group_state(self, group_id: int) -> Optional[str]:
        with self._lock:
            cmd = self._commanders.get(group_id)
            return cmd.current_state if cmd else None

    def get_participants(self, group_id: int) -> List[Actor]:
        with self._lock:
            worker = self._workers.get(group_id)
        if not worker:
            return []
        return worker.get_participants_snapshot()

    def get_last_snapshot_ts(self, group_id: int) -> Optional[float]:
        with self._lock:
            worker = self._workers.get(group_id)
        if not worker:
            return None
        return worker.last_snapshot_time()


# =================== 使用示例 ===================
if __name__ == "__main__":
    api = GameAPI()  # 你的游戏 API 实例
    monitor = GroupMonitor(api)
    monitor.start()

    # 启动 group 1 攻击
    monitor.start_group(group_id=1, state=AttackState.ATTACK)

    # 启动 group 2 防御
    monitor.start_group(group_id=2, state=AttackState.DEFENSE)

    # 主循环中查询状态
    try:
        while True:
            for gid in monitor.list_groups():
                print(f"Group {gid}: running={monitor.is_group_running(gid)}, fighting={monitor.is_group_fighting(gid)}, participants={len(monitor.get_participants(gid))}")
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("Stopping monitor...")
        monitor.stop()
