from typing import List
import numpy as np
from OpenRA_Copilot_Library.models import Actor, MapQueryResult

### Map
class Map:
    def __init__(self, llm_width:int = 10, llm_height:int = 10):
        self.llm_width = llm_width
        self.llm_height = llm_height
        self.width = 0
        self.height = 0
        self.map_cache = None
        self.llm_map:str = None

    def __init_map(self, width:int, height:int):
        self.width = width
        self.height = height
        # 修正初始化时维度顺序，高度在前，宽度在后
        self.map_cache = np.full((self.height, self.width), False, dtype=bool)


    def update_map_cache(self, map_query_result: MapQueryResult, actors: List[Actor]):
        if self.map_cache is None and map_query_result:
            self.__init_map(width=map_query_result.MapWidth, height=map_query_result.MapHeight)

        for actor in actors:
            self.map_cache[actor.position.x, actor.position.y] = True

    def to_llm(self) -> str:
        # 计算补零后能被整除的新尺寸
        new_width = ((self.width + self.llm_width - 1) // self.llm_width) * self.llm_width
        new_height = ((self.height + self.llm_height - 1) // self.llm_height) * self.llm_height
        
        # 计算四个方向的补零量
        pad_dims = (new_height - self.height, new_width - self.width)
        pad_spec = ((pad_dims[0] // 2, pad_dims[0] - pad_dims[0] // 2),
                    (pad_dims[1] // 2, pad_dims[1] - pad_dims[1] // 2))

        # 转换类型并补零
        llm_map = np.pad(self.map_cache.astype(int), pad_spec, mode='constant')

        # 定义网格大小并重塑数组，确保维度顺序正确
        grid_width = new_width // self.llm_width
        grid_height = new_height // self.llm_height
        # 修正 reshape 时的维度顺序，高度在前，宽度在后
        pooled_map = llm_map.reshape(
            self.llm_height, grid_height, self.llm_width, grid_width
        ).sum(axis=(1, 3))

        # 使用列表推导式生成结果字符串
        grid_area = grid_width * grid_height
        self.llm_map = '\n'.join(
            ' | '.join(
                f'{count}/{grid_area}' if count > 0 else '0'
                for count in row
            ) for row in pooled_map
        )
        return self.llm_map