from typing import List
from OpenRA_Copilot_Library.models import Actor, TargetsQueryParam
from .map import Map
from collections import defaultdict
from ..mcp_server import BUILDING, game_api
import traceback
import configs
from multiprocessing import shared_memory


class DefenseMonitor:
    def __init__(self, map: Map):
        self.map = map
        self.last_actors = {} # 己方 actor id -> actor
        self.shm = None


    def be_attacked(self, actors: List[Actor]):
        be_attacked_actors = defaultdict(list)
        for actor in actors:
            if actor.faction == "己方":
                if actor.actor_id in self.last_actors:
                    if self.last_actors[actor.actor_id].hppercent > actor.hppercent:
                        key = "building" if actor.type in BUILDING else "infantry"
                        be_attacked_actors[key].append(actor)


        # clear last actors
        self.last_actors.clear()
        for actor in actors:
            self.last_actors[actor.actor_id] = actor

        return be_attacked_actors
    

    def auto_monitor(self):
        map_info = game_api.map_query() if self.map.map_cache is None else None
        actors = game_api.query_actor(query_params=TargetsQueryParam(faction="己方"))
        self.map.update_map_cache(map_info, actors)

        try:
            llm_map = self.map.to_llm()
            data_bytes = llm_map.encode('utf-8')
            if self.shm is None:
                try:
                    # Attempt to create new shared memory
                    self.shm = shared_memory.SharedMemory(name=configs.GLOBAL_STATE.SHARED_LLM_MAP_NAME, create=True, size=4096)
                except FileExistsError:
                    # If exists, connect to existing shared memory
                    self.shm = shared_memory.SharedMemory(name=configs.GLOBAL_STATE.SHARED_LLM_MAP_NAME, create=False)
                
            self.shm.buf[:len(data_bytes)] = data_bytes
            # print(f"[INFO] Update LLM Map success, map size: {len(data_bytes)}")

        except Exception as ex:
            print(f"[ERROR] Update LLM Map error: {ex}")
            traceback.print_exc()
        
        be_attacked_actors = self.be_attacked(actors)
        if "building" in be_attacked_actors:
            print("!!!!!!!! warning: building is under attack: ", be_attacked_actors["building"])
        if "infantry" in be_attacked_actors:
            print("!!!!!!!! warning: infantry is under attack: ", be_attacked_actors["infantry"])


    def __del__(self):
        if self.shm is not None:
            self.shm.close()
            self.shm.unlink()
