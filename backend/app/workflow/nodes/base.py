from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any, ClassVar, Generic, TypeVar

from pydantic import BaseModel, Field

from ..variable_pool import VariablePool


class RunStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"


class NodeRunResult(BaseModel):
    """单个节点的执行结果。

    Dify 针对不同节点类型定义了各自的 Result 子类
    （LLMNodeResult / CodeNodeResult / KnowledgeRetrievalNodeResult 等），
    每种结果携带节点专属字段（如 LLM 的 usage token 数量）。
    我们统一用一个通用结构：outputs 存所有产出变量，需要节点专属字段时再继承扩展。
    """

    status: RunStatus
    outputs: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


# NodeDataT 是每个节点自己的静态配置类型，必须是 Pydantic BaseModel。
# 对应 Dify 的 Generic[T] 模式，用 TypeVar + bound 约束保证类型安全。
NodeDataT = TypeVar("NodeDataT", bound=BaseModel)


class BaseNode(ABC, Generic[NodeDataT]):
    """所有节点的抽象基类。

    两个核心设计决策：

    1. Generic[NodeDataT] — Config vs Variable 解耦
       node_data  = 静态配置（workflow 定义时写死，如 model 名称、prompt 模板）
       variable_pool = 运行时数据（每次 run 动态流入，如上一个节点的输出文本）
       两者分离意味着同一份 workflow 定义可以用不同数据跑无数次。

    2. run() / _run() — Template Method 模式
       run()  负责公共流程：把 _run() 的 outputs 写入 pool、统一捕获异常
       _run() 只管节点自身逻辑，不碰 pool，不处理异常
       Dify 的 run() 还会 emit NodeStartedEvent / NodeFinishedEvent 给前端推送，
       我们省略事件系统，执行状态由 engine 层统一记录即可。
    """

    # 子类用 ClassVar 声明自己的节点类型，引擎通过它把字符串路由到对应类。
    # Dify 用 _node_type: NodeType，我们命名为 node_type，更直白。
    node_type: ClassVar[str]

    def __init__(
        self,
        node_id: str,
        node_data: NodeDataT,
        variable_pool: VariablePool,
    ) -> None:
        self.node_id = node_id
        self.node_data = node_data          # 静态 config，类型由 NodeDataT 保证
        self.variable_pool = variable_pool  # 运行时共享状态

    async def run(self) -> NodeRunResult:
        """Template Method：公共流程在这里，子类专注 _run()。

        Dify 还在这里处理 GraphRuntimeState 更新（节点状态机）和
        parallel branch 的并发控制，我们不做暂停/恢复，省略这部分。
        """
        try:
            result = await self._run()
        except Exception as exc:
            return NodeRunResult(status=RunStatus.FAILED, error=str(exc))

        # 成功时把 outputs 统一写入 VariablePool，供下游节点通过 selector 读取。
        # Dify 在各节点内部自行写 pool，我们集中在基类做，减少子类重复代码。
        if result.status == RunStatus.SUCCESS:
            for key, value in result.outputs.items():
                self.variable_pool.add([self.node_id, key], value)

        return result

    @abstractmethod
    async def _run(self) -> NodeRunResult:
        """子类实现节点核心逻辑。

        规则：
        - 只读 self.node_data（静态配置）和 self.variable_pool（上游数据）
        - 把本节点产出放进 NodeRunResult.outputs，不要直接写 pool
        - 抛异常即可，run() 会统一捕获转为 FAILED 状态
        """
        ...
