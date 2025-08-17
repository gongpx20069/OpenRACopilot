from .map_monitor.monitor import DefenseMonitor
from .map_monitor.map import Map

GLOBAL_MAP = Map()
DEFENSE_MONITOR = DefenseMonitor(GLOBAL_MAP)


def schedule_monitor(sc, interval: int = 3):
    """
    间隔interval秒触发一次地图监控
    """
    # print(f"[SCHEDULE] Map Monitoring Update - {interval}s")
    DEFENSE_MONITOR.auto_monitor()
    # print("[ENDING] Map Monitoring Update")

    # 间隔interval秒触发 invterval 
    sc.enter(interval, 1, schedule_monitor, (sc, interval))