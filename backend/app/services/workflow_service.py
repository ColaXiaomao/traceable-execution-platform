"""workflow 执行服务。

负责把 workflow engine（底层基础设施）和业务层连接起来：
  - 注入外部依赖（db session、artifact_store）给需要的节点
  - 返回 engine 的执行结果供 API 层使用

service 层的职责边界：
  - 知道「这个工单要跑哪个 workflow」（业务逻辑）
  - 不知道「workflow 内部节点怎么跑」（引擎职责）
  - 不直接操作 VariablePool（引擎职责）
"""

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from ..storage.artifact_store import artifact_store
from ..workflow.definitions.router_config_analysis import ROUTER_CONFIG_ANALYSIS
from ..workflow.engine import WorkflowEngine, WorkflowRunResult


async def run_router_config_analysis(
    db: AsyncSession,
    ticket_id: int,
    artifact_id: int,
    triggered_by: User,
) -> WorkflowRunResult:
    """对工单绑定的路由器配置文件执行 LLM 分析 workflow。

    调用 WorkflowEngine，注入 db/artifact_store 依赖，分析结果作为
    新 artifact 保存到工单下。

    返回：WorkflowRunResult
    调用方（API 层）可从 result.outputs 拿到分析文本和新 artifact ID。
    """
    engine = WorkflowEngine()
    return await engine.run(
        definition=ROUTER_CONFIG_ANALYSIS,
        user_inputs={"artifact_id": artifact_id},
        system_variables={
            "user_id": triggered_by.id,
            "ticket_id": ticket_id,
        },
        node_context={
            "db": db,
            "artifact_store": artifact_store,
        },
    )
