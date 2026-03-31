from __future__ import annotations

from pydantic import BaseModel, Field

from ..types import NodeType
from .base import BaseNode, NodeRunResult, RunStatus


class OutputVariableDeclaration(BaseModel):
    """声明 workflow 最终对外暴露哪些变量。

    name     : 最终结果里的 key 名称
    selector : 从 VariablePool 哪个位置读取，对应 [node_id, var_name]

    Dify 的 EndNode outputs 定义里还包含 value_selector（与我们的 selector 等价）
    以及 output_type（string / number / object 等），用于前端渲染。
    我们省略 output_type，类型信息已经在 Variable 对象上，不需要重复声明。
    """

    name: str
    selector: list[str]


class EndNodeData(BaseModel):
    """EndNode 的静态配置：声明 workflow 的最终输出变量列表。"""

    outputs: list[OutputVariableDeclaration] = Field(default_factory=list)


class EndNode(BaseNode[EndNodeData]):
    """workflow 的出口节点，从 VariablePool 收集最终结果并返回。

    EndNode 的 outputs 不会写回 pool（结果直接给 engine 消费），
    但基类 run() 仍会把它们写入 end.* 命名空间，
    方便 snapshot() 审计时看到完整的执行链路。
    """

    node_type = NodeType.END

    async def _run(self) -> NodeRunResult:
        result: dict = {}
        missing: list[str] = []

        for decl in self.node_data.outputs:
            value = self.variable_pool.get_value(decl.selector)
            if value is None:
                missing.append(f"{decl.name} <- {decl.selector}")
            else:
                result[decl.name] = value

        if missing:
            return NodeRunResult(
                status=RunStatus.FAILED,
                error=f"EndNode 找不到以下输出变量：{missing}",
            )

        return NodeRunResult(status=RunStatus.SUCCESS, outputs=result)
