from .mcp_server import game_api
from .monitor.map_monitor import DefenseMonitor
from .monitor.map import Map
from .monitor.group_commander_monitor import GroupMonitor

GLOBAL_MAP = Map()
DEFENSE_MONITOR = DefenseMonitor(GLOBAL_MAP)
GROUP_COMMANDER_MONITOR = GroupMonitor(api=game_api, tick=1)

def schedule_monitor(sc, interval: int = 3):
    """
    间隔interval秒触发一次地图监控
    """
    # print(f"[SCHEDULE] Map Monitoring Update - {interval}s")
    DEFENSE_MONITOR.auto_monitor()
    # print("[ENDING] Map Monitoring Update")

    # 间隔interval秒触发 invterval 
    sc.enter(interval, 1, schedule_monitor, (sc, interval))