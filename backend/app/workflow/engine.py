from __future__ import annotations

from typing import Any, get_args

from pydantic import BaseModel, Field

from .nodes.base import BaseNode, NodeRunResult, RunStatus
from .nodes.end import EndNode
from .nodes.llm_node import LLMNode
from .nodes.start import StartNode
from .types import NodeType
from .variable_pool import VariablePool


# ---------------------------------------------------------------------------
# Workflow 定义结构（静态，描述 DAG 长什么样）
# ---------------------------------------------------------------------------


class NodeDefinition(BaseModel):
    """单个节点的定义。

    id   : 节点在本 workflow 内的唯一标识，同时作为 VariablePool 的命名空间。
    type : 对应 NodeType 枚举，引擎通过它找到实际的节点类。
    data : 节点的静态配置，会被解析成对应的 NodeDataT（如 LLMNodeData）。

    Dify 的节点定义还包含 position（画布坐标）和 title/desc（UI 展示）等字段，
    我们只保留运行时必须的三个字段，UI 信息不影响执行语义。
    """

    id: str
    type: NodeType
    data: dict[str, Any] = Field(default_factory=dict)


class EdgeDefinition(BaseModel):
    """有向边：source 节点跑完后才执行 target 节点。

    Dify 的 edge 还有 run_condition（条件路由：上游节点输出满足某条件才走这条边），
    用于实现 if/else 分支。我们只做无条件顺序边，条件分支未来有需要再加。
    """

    source: str
    target: str


class WorkflowDefinition(BaseModel):
    """完整的 workflow 定义，由 nodes + edges 描述一个 DAG。

    Dify 把 Graph 单独抽成一个类，负责 DAG 校验、可达性分析、
    并行分支识别等复杂逻辑。我们的图结构足够简单，
    把拓扑排序和校验内联在 engine 里，不需要独立的 Graph 类。
    """

    nodes: list[NodeDefinition]
    edges: list[EdgeDefinition]


# ---------------------------------------------------------------------------
# 执行结果
# ---------------------------------------------------------------------------


class WorkflowRunResult(BaseModel):
    """一次 workflow 执行的最终结果。

    outputs  : EndNode 收集的输出变量，直接透传给调用方（service 层）。
    snapshot : pool.snapshot() 的内容，记录所有节点的完整输出，
               供写入 Run.execution_context 做审计追踪。

    Dify 通过 async generator yield WorkflowRunStreamChunkResponse 流式返回，
    每个节点跑完就推一帧给前端。我们返回一个完整结果对象，
    流式支持未来有需要时改成 AsyncGenerator 即可。
    """

    status: RunStatus
    outputs: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    snapshot: dict[str, dict[str, Any]] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# 节点注册表：NodeType → 节点类
# ---------------------------------------------------------------------------

# Dify 用动态扫描（metaclass 自动注册所有 BaseNode 子类）。
# 我们用显式字典，更直白，也避免了 import 顺序依赖。
# 新增节点类型时：在 NodeType 枚举里加值，在这里加一行映射即可。
_NODE_REGISTRY: dict[NodeType, type[BaseNode]] = {
    NodeType.START: StartNode,
    NodeType.END: EndNode,
    NodeType.LLM: LLMNode,
}


# ---------------------------------------------------------------------------
# WorkflowEngine
# ---------------------------------------------------------------------------


class WorkflowEngine:
    """执行引擎：接收 workflow 定义 + 输入，顺序跑完所有节点，返回最终结果。

    设计原则：
    - engine 只负责调度（排序、循环、失败处理），不包含任何业务逻辑
    - 业务逻辑全部在各 Node._run() 里
    - VariablePool 是唯一的节点间通信通道，engine 不直接传数据给节点

    Dify 的 WorkflowEngineManager 还处理：
    - 并行分支（parallel node group，多个节点同时 asyncio.gather）
    - 循环节点（iteration node，内嵌子 workflow）
    - 执行超时控制
    我们只做线性顺序执行，这三点未来按需扩展。
    """

    async def run(
        self,
        definition: WorkflowDefinition,
        user_inputs: dict[str, Any],
        system_variables: dict[str, Any] | None = None,
    ) -> WorkflowRunResult:
        """执行一个 workflow。

        Args:
            definition:       workflow 的 DAG 定义
            user_inputs:      本次运行的初始输入（由 StartNode 写入 start.* 命名空间）
            system_variables: 系统级变量（user_id / ticket_id 等，写入 sys.* 命名空间）
        """
        pool = VariablePool.create(
            system_variables=system_variables,
            user_inputs=user_inputs,
        )

        # 拓扑排序：确定节点执行顺序
        try:
            ordered_nodes = _topological_sort(definition)
        except ValueError as exc:
            return WorkflowRunResult(status=RunStatus.FAILED, error=str(exc))

        # 按序执行每个节点
        end_result: NodeRunResult | None = None
        for node_def in ordered_nodes:
            node = _build_node(node_def, pool)
            result = await node.run()

            if result.status == RunStatus.FAILED:
                return WorkflowRunResult(
                    status=RunStatus.FAILED,
                    error=f"节点 [{node_def.id}({node_def.type})] 执行失败: {result.error}",
                    snapshot=pool.snapshot(),
                )

            if node_def.type == NodeType.END:
                end_result = result

        return WorkflowRunResult(
            status=RunStatus.SUCCESS,
            outputs=end_result.outputs if end_result else {},
            snapshot=pool.snapshot(),
        )


# ---------------------------------------------------------------------------
# 内部工具函数
# ---------------------------------------------------------------------------


def _topological_sort(definition: WorkflowDefinition) -> list[NodeDefinition]:
    """Kahn 算法（BFS）拓扑排序，同时检测环。

    Dify 在 Graph 类里用 DFS 做拓扑排序并支持并行层级识别
    （同一层的节点可以并发执行）。我们用 Kahn 算法做线性排序，
    逻辑更简单，也足以支持未来扩展并行时按层分组。
    """
    node_map = {n.id: n for n in definition.nodes}
    in_degree: dict[str, int] = {n.id: 0 for n in definition.nodes}
    adjacency: dict[str, list[str]] = {n.id: [] for n in definition.nodes}

    for edge in definition.edges:
        if edge.source not in node_map or edge.target not in node_map:
            raise ValueError(f"边引用了不存在的节点：{edge.source} → {edge.target}")
        adjacency[edge.source].append(edge.target)
        in_degree[edge.target] += 1

    # 入度为 0 的节点先入队（通常只有 StartNode）
    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    ordered: list[NodeDefinition] = []

    while queue:
        nid = queue.pop(0)
        ordered.append(node_map[nid])
        for neighbor in adjacency[nid]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(ordered) != len(definition.nodes):
        raise ValueError("workflow 定义中存在循环依赖，无法执行")

    return ordered


def _build_node(node_def: NodeDefinition, pool: VariablePool) -> BaseNode:
    """根据节点定义实例化对应的节点类。

    核心步骤：
    1. 从注册表拿到节点类（如 LLMNode）
    2. 从 Generic[NodeDataT] 的泛型参数反射出 NodeDataT（如 LLMNodeData）
    3. 用 node_def.data 解析成强类型的 config 对象
    4. 构造节点实例，注入 node_id / node_data / variable_pool

    Dify 用显式的 _node_data_cls 类变量避免运行时反射，
    我们用 __orig_bases__ + get_args() 动态提取，
    好处是子类不需要额外声明，代价是多一次反射调用（性能可忽略）。
    """
    node_cls = _NODE_REGISTRY.get(node_def.type)
    if node_cls is None:
        raise ValueError(f"未注册的节点类型：{node_def.type}，请在 _NODE_REGISTRY 中添加")

    data_cls = _extract_node_data_cls(node_cls)
    node_data = data_cls(**node_def.data)

    return node_cls(node_id=node_def.id, node_data=node_data, variable_pool=pool)


def _extract_node_data_cls(node_cls: type[BaseNode]) -> type[BaseModel]:
    """从 BaseNode[NodeDataT] 的泛型声明中提取 NodeDataT 的实际类型。"""
    for base in getattr(node_cls, "__orig_bases__", []):
        args = get_args(base)
        if args and isinstance(args[0], type) and issubclass(args[0], BaseModel):
            return args[0]
    raise TypeError(f"无法从 {node_cls.__name__} 提取 NodeDataT，请确保继承自 BaseNode[YourNodeData]")
