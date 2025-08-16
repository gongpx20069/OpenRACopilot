-----

### 游戏服务器连接和状态检查工具

| 函数名 | 函数描述 | 输入描述 | 输出描述 |
| :--- | :--- | :--- | :--- |
| `is_server_running` | 检查游戏服务器是否已启动并可访问 | `host` (str): 游戏服务器地址，默认为 `"localhost"`。\<br\>`port` (int): 游戏服务器端口，默认为 `7445`。\<br\>`timeout` (float): 连接超时时间（秒），默认为 `2.0` 秒。 | `bool`: 服务器是否已启动并可访问 |

-----

### 基础API通信工具

| 函数名 | 函数描述 | 输入描述 | 输出描述 |
| :--- | :--- | :--- | :--- |
| `__init__` | 初始化 `GameAPI` 类 | `host` (str): 游戏服务器地址，本地就填 `"localhost"`。\<br\>`port` (int): 游戏服务器端口，默认为 `7445`。\<br\>`language` (str): 接口返回语言，默认为 `"zh"`，支持 `"zh"` 和 `"en"`。 | 无 |
| `_generate_request_id` | 生成唯一的请求ID | 无 | `str`: 唯一的请求ID |
| `_send_request` | 通过 `socket` 和游戏交互，发送信息并接收响应 | `command` (str): 要执行的命令\<br\>`params` (dict): 命令相关的数据参数 | `dict`: 服务器返回的JSON响应数据 |
| `_receive_data` | 从 `socket` 接收完整的响应数据 | `sock` (`socket.socket`): 套接字对象 | `str`: 完整的响应数据 |
| `_handle_response` | 处理API响应，提取所需数据或抛出异常 | `response` (dict): API响应数据\<br\>`error_msg` (str): 错误信息 | `Any`: 响应中的数据，若无则返回响应本身 |

-----

### 相机控制工具

| 函数名 | 函数描述 | 输入描述 | 输出描述 |
| :--- | :--- | :--- | :--- |
| `move_camera_by_location` | 根据给定的位置移动相机 | `location` (`Location`): 要移动到的位置 | 无 |
| `move_camera_by_direction` | 向某个方向移动相机 | `direction` (str): 移动的方向，必须在 `{ALL_DIRECTIONS}` 中\<br\>`distance` (int): 移动的距离 | 无 |
| `move_camera_to` | 将相机移动到指定Actor位置 | `actor` (`Actor`): 目标Actor | 无 |

-----

### 生产和建筑工具

| 函数名 | 函数描述 | 输入描述 | 输出描述 |
| :--- | :--- | :--- | :--- |
| `can_produce` | 检查是否可以生产指定类型的Actor | `unit_type` (str): Actor类型，必须在 `{ALL_UNITS}` 中 | `bool`: 是否可以生产 |
| `produce` | 生产指定数量的Actor | `unit_type` (str): Actor类型\<br\>`quantity` (int): 生产数量\<br\>`auto_place_building` (bool, optional): 是否在生产完成后使用随机位置自动放置建筑，仅对建筑类型有效 | `int`: 生产任务的 `waitId`\<br\>`None`: 如果任务创建失败 |
| `produce_wait` | 生产指定数量的Actor并等待生产完成 | `unit_type` (str): Actor类型\<br\>`quantity` (int): 生产数量\<br\>`auto_place_building` (bool, optional): 是否在生产完成后使用随机位置自动放置建筑，仅对建筑类型有效 | 无 |
| `is_ready` | 检查生产任务是否完成 | `wait_id` (int): 生产任务的 ID | `bool`: 是否完成 |
| `wait` | 等待生产任务完成 | `wait_id` (int): 生产任务的 ID\<br\>`max_wait_time` (float): 最大等待时间，默认为 20 秒 | `bool`: 是否成功完成等待（`False` 表示超时） |
| `query_production_queue` | 查询指定类型的生产队列 | `queue_type` (str): 队列类型，必须是以下值之一：`'Building'`, `'Defense'`, `'Infantry'`, `'Vehicle'`, `'Aircraft'`, `'Naval'` | `dict`: 包含队列信息的字典 |
| `place_building` | 放置建造队列顶端已就绪的建筑 | `queue_type` (str): 队列类型，可选值：`'Building'`, `'Defense'`, `'Infantry'`, `'Vehicle'`, `'Aircraft'`, `'Naval'`\<br\>`location` (`Location`, optional): 放置建筑的位置，如果不指定则使用自动选择的位置 | 无 |
| `manage_production` | 管理生产队列中的项目（暂停/取消/继续） | `queue_type` (str): 队列类型，可选值：`'Building'`, `'Defense'`, `'Infantry'`, `'Vehicle'`, `'Aircraft'`, `'Naval'`\<br\>`action` (str): 操作类型，必须是 `'pause'`, `'cancel'`, 或 `'resume'` | 无 |
| `deploy_mcv_and_wait` | 展开自己的基地车并等待一小会 | `wait_time` (float): 展开后的等待时间(秒)，默认为1秒，一般不用改 | 无 |
| `ensure_can_build_wait` | 确保能生产某个建筑，如果不能会尝试生产所有前置建筑，并等待生产完成 | `building_name` (str): 建筑名称(中文) | `bool`: 是否已经拥有该建筑或成功生产 |
| `ensure_building_wait_buildself` | 非外部接口，确保能生产某个建筑并等待完成 | `building_name` (str): 建筑名称(中文) | `bool`: 是否成功生产 |
| `ensure_can_produce_unit` | 确保能生产某个Actor(会自动生产其所需建筑并等待完成) | `unit_name` (str): Actor名称(中文) | `bool`: 是否成功准备好生产该Actor |
| `set_rally_point` | 设置建筑的集结点 | `actors` (list[`Actor`]): 要设置集结点的建筑列表\<br\>`target_location` (`Location`): 集结点目标位置 | 无 |

-----

### 单位操作和移动工具

| 函数名 | 函数描述 | 输入描述 | 输出描述 |
| :--- | :--- | :--- | :--- |
| `move_units_by_location` | 移动单位到指定位置 | `actors` (List[`Actor`]): 要移动的Actor列表\<br\>`location` (`Location`): 目标位置\<br\>`attack_move` (bool): 是否为攻击性移动 | 无 |
| `move_units_by_direction` | 向指定方向移动单位 | `actors` (List[`Actor`]): 要移动的Actor列表\<br\>`direction` (str): 移动方向\<br\>`distance` (int): 移动距离 | 无 |
| `move_units_by_path` | 沿路径移动单位 | `actors` (List[`Actor`]): 要移动的Actor列表\<br\>`path` (List[`Location`]): 移动路径 | 无 |
| `select_units` | 选中符合条件的Actor，指的是游戏中的选中操作 | `query_params` (`TargetsQueryParam`): 查询参数 | 无 |
| `form_group` | 将Actor编成编组 | `actors` (List[`Actor`]): 要分组的Actor列表\<br\>`group_id` (int): 群组 ID | 无 |
| `deploy_units` | 部署/展开 Actor | `actors` (List[`Actor`]): 要部署/展开的Actor列表 | 无 |
| `occupy_units` | 占领目标 | `occupiers` (List[`Actor`]): 执行占领的Actor列表\<br\>`targets` (List[`Actor`]): 被占领的目标列表 | 无 |
| `attack_target` | 攻击指定目标 | `attacker` (`Actor`): 发起攻击的Actor\<br\>`target` (`Actor`): 被攻击的目标 | `bool`: 是否成功发起攻击(如果目标不可见，或者不可达，或者攻击者已经死亡，都会返回 `False`) |
| `can_attack_target` | 检查是否可以攻击目标 | `attacker` (`Actor`): 攻击者\<br\>`target` (`Actor`): 目标 | `bool`: 是否可以攻击 |
| `repair_units` | 修复Actor | `actors` (List[`Actor`]): 要修复的Actor列表，可以是载具或者建筑，修理载具需要修建修理中心 | 无 |
| `stop` | 停止Actor当前行动 | `actors` (List[`Actor`]): 要停止的Actor列表 | 无 |
| `move_units_by_location_and_wait` | 移动一批Actor到指定位置，并等待(或直到超时) | `actors` (List[`Actor`]): 要移动的Actor列表\<br\>`location` (`Location`): 目标位置\<br\>`max_wait_time` (float): 最大等待时间(秒)\<br\>`tolerance_dis` (int): 容忍的距离误差，Actor越多一般就得设得越大 | `bool`: 是否在 `max_wait_time` 内到达(若中途卡住或超时则 `False`) |

-----

### 信息查询和感知工具

| 函数名 | 函数描述 | 输入描述 | 输出描述 |
| :--- | :--- | :--- | :--- |
| `query_actor` | 查询符合条件的Actor，获取Actor应该使用的接口 | `query_params` (`TargetsQueryParam`): 查询参数 | List[`Actor`]: 符合条件的Actor列表 |
| `find_path` | 为Actor找到到目标的路径 | `actors` (List[`Actor`]): 要移动的Actor列表\<br\>`destination` (`Location`): 目标位置\<br\>`method` (str): 寻路方法，必须在 `{"最短路", "左路", "右路"}` 中 | List[`Location`]: 路径点列表，第0个是目标点，最后一个是Actor当前位置，相邻的点都是八方向相连的点 |
| `get_actor_by_id` | 获取指定 ID 的Actor，这是根据ActorID获取Actor的接口，只有已知ActorID是才能调用这个接口 | `actor_id` (int): Actor ID | `Actor`: 对应的Actor\<br\>`None`: 如果Actor不存在 |
| `update_actor` | 更新Actor信息，如果时间改变了，需要调用这个来更新Actor的各种属性（位置等） | `actor` (`Actor`): 要更新的Actor | `bool`: 如果Actor已死，会返回 `False`，否则返回 `True` |
| `visible_query` | 查询位置是否可见 | `location` (`Location`): 要查询的位置 | `bool`: 是否可见 |
| `explorer_query` | 查询位置是否已探索 | `location` (`Location`): 要查询的位置 | `bool`: 是否已探索 |
| `get_unexplored_nearby_positions` | 获取当前位置附近尚未探索的坐标列表 | `map_query_result` (`MapQueryResult`): 地图信息\<br\>`current_pos` (`Location`): 当前Actor的位置\<br\>`max_distance` (int): 距离范围(曼哈顿) | List[`Location`]: 未探索位置列表 |
| `unit_attribute_query` | 查询Actor的属性和攻击范围内目标 | `actors` (List[`Actor`]): 要查询的Actor列表 | `dict`: Actor属性信息，包括攻击范围内的目标 |
| `unit_range_query` | 获取这些传入Actor攻击范围内的所有Target (已弃用，请使用 `unit_attribute_query`) | `actors` (List[`Actor`]): 要查询的Actor列表 | List[`int`]: 攻击范围内的目标ID列表 |
| `map_query` | 查询地图信息 | 无 | `MapQueryResult`: 地图查询结果 |
| `player_base_info_query` | 查询玩家基地信息 | 无 | `PlayerBaseInfo`: 玩家基地信息 |
| `screen_info_query` | 查询当前玩家看到的屏幕信息 | 无 | `ScreenInfoResult`: 屏幕信息查询结果 |