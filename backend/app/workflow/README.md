# Workflow 模块

## 概览

本模块是 Traceable Execution Platform 的 workflow 执行引擎，参考 Dify 的架构思路，
针对本项目的业务场景（artifact 自动分析）做了大幅简化和针对性设计。

当前已实现的 workflow：
- **路由器配置 LLM 分析**：读取工单下的路由器配置 artifact，调用 LLM 生成安全评价报告，结果持久化为新 artifact

---

## 架构

```
workflow/
├── engine.py            # 执行引擎：拓扑排序 + 顺序调度
├── variable_pool.py     # 变量池：节点间唯一通信通道
├── variable.py          # 变量类型系统
├── types.py             # 枚举定义（NodeType / SegmentType / Selector）
├── nodes/
│   ├── base.py          # BaseNode 抽象基类
│   ├── start.py         # 入口节点
│   ├── end.py           # 出口节点
│   ├── llm_node.py      # LLM 调用节点（通过 LiteLLM 网关）
│   ├── artifact_loader.py  # 从存储层读取 artifact 内容
│   └── artifact_saver.py   # 把内容持久化为 artifact
└── definitions/
    └── router_config_analysis.py  # 路由器配置分析 workflow 定义
```

### 核心组件

**WorkflowEngine**（`engine.py`）

引擎的唯一入口。接收 workflow 定义（DAG）和运行时输入，
执行拓扑排序后顺序调度每个节点，返回 `WorkflowRunResult`。

**VariablePool**（`variable_pool.py`）

节点间共享数据的唯一通道。内部是两层字典 `{node_id: {var_name: Variable}}`，
节点通过 `[node_id, var_name]` 格式的 selector 读写变量，命名空间天然隔离。
还支持 `{{node_id.var_name}}` 模板语法解析，供 LLMNode 构建 prompt 使用。

**BaseNode**（`nodes/base.py`）

所有节点的抽象基类，用 Template Method 模式将公共流程与节点逻辑分离：
- `run()`：公共流程，负责把 `_run()` 的 outputs 统一写入 VariablePool、捕获异常
- `_run()`：子类实现，只管节点自身逻辑，不直接操作 pool，不处理异常

**WorkflowDefinition**（`engine.py`）

workflow 的静态描述，由 `nodes`（节点列表）和 `edges`（有向边列表）构成一个 DAG。
当前 workflow 定义以代码形式写在 `definitions/` 目录下。

---

## 与 Dify 的核心差异

### 1. 线性执行 vs 并行调度

Dify 的 graph engine 支持并行分支：多个前驱都完成后，节点进入 `ready_queue`，
由调度循环用 `asyncio.gather` 并发执行同一层的节点。

本引擎只做**线性顺序执行**：拓扑排序在执行前一次性完成，得到一个有序列表，
engine 直接 `for` 循环依次 `await`，不需要运行时动态队列。
好处是逻辑极简，坏处是无法并行；当前业务场景是单链路，够用。

### 2. 无事件系统

Dify 的节点执行会 emit `NodeRunStartedEvent / NodeRunSucceededEvent / NodeRunFailedEvent`，
通过 async generator 流式推送给前端，实现执行过程的实时可视化。

本引擎省略了事件系统，执行完成后返回一个完整的 `WorkflowRunResult`，
包含最终输出和全量变量快照（`snapshot`），由调用方决定如何使用。
流式支持未来有需要时改成 `AsyncGenerator` 即可。

### 3. 显式 context 注入 vs 框架 DI

Dify 节点内部通过 Flask/FastAPI 的依赖注入框架直接拿到 db session 等外部依赖。

本引擎通过 `node_context` 参数显式传入，调用链一目了然：

```python
await engine.run(
    definition=ROUTER_CONFIG_ANALYSIS,
    user_inputs={"artifact_id": 42},
    system_variables={"user_id": 1, "ticket_id": 10},
    node_context={"db": db, "artifact_store": artifact_store},
)
```

好处是调用链清晰，测试时直接 mock dict 即可，不需要 override 依赖注入。

### 4. 显式节点注册表 vs 元类自动注册

Dify 用 metaclass 扫描所有 `BaseNode` 子类自动注册，新加节点无需额外操作。

本引擎在 `engine.py` 维护一个显式字典：

```python
_NODE_REGISTRY: dict[NodeType, type[BaseNode]] = {
    NodeType.START: StartNode,
    NodeType.END: EndNode,
    NodeType.LLM: LLMNode,
    NodeType.ARTIFACT_LOADER: ArtifactLoaderNode,
    NodeType.ARTIFACT_SAVER: ArtifactSaverNode,
}
```

好处是一目了然，没有隐式魔法，import 顺序不会造成注册遗漏。

### 5. 变量系统简化

Dify 将 `Segment`（值的存储）和 `Variable`（变量身份）分成两个独立类层级，
并通过 `SegmentGroup` 支持模板片段的类型感知拼接。

本引擎将两者合并为单一的 `Variable` 类，`resolve_template` 直接返回拼接好的字符串，
去掉 `SegmentGroup` 中间层。当前节点只需要把值插入 prompt，不需要感知片段类型。

### 6. LLMNode 调用方式

Dify 内部有完整的 `ModelManager` 抽象层，支持多租户 API key 管理、provider 路由、
用量统计、streaming 推送、tool calling 等，LLMNode 通过这一套框架调用模型。

本引擎的 LLMNode 直接用 `httpx` POST 到 **LiteLLM Gateway**，由 LiteLLM 负责 provider 路由：

```
LLMNode → httpx POST → LiteLLM Gateway → ollama/mistral（本地）
                                        → OpenAI / Claude（云端）
```

model 名称在 workflow 定义里配置（如 `local-mistral`），
LiteLLM 的路由规则在 `docker/litellm-config.yaml` 里维护，两者解耦。
省略了 Dify LLMNode 中的 streaming、tool calling 和 token 用量统计，
当前场景只需要拿到完整的文本响应即可。

### 7. 业务专属节点

Dify 的节点都是通用的（Code、HTTP Request、Knowledge Retrieval 等）。

本引擎额外实现了两个与 artifact 基础设施深度集成的专属节点：
- **ArtifactLoaderNode**：通过 db 查 `storage_path`，再用 `artifact_store` 读文件字节，输出文本
- **ArtifactSaverNode**：把文本编码后存入 `artifact_store`，同时在 db 创建 `Artifact` 记录

---

## 新增节点

1. 在 `nodes/` 下新建节点文件，继承 `BaseNode[YourNodeData]`
2. 实现 `_run()` 方法，返回 `NodeRunResult`
3. 在 `types.py` 的 `NodeType` 枚举中添加新类型
4. 在 `engine.py` 的 `_NODE_REGISTRY` 中注册映射

```python
# types.py
class NodeType(StrEnum):
    YOUR_NODE = "your_node"

# engine.py
_NODE_REGISTRY = {
    ...
    NodeType.YOUR_NODE: YourNode,
}
```

## 新增 Workflow 定义

在 `definitions/` 下新建文件，用 `WorkflowDefinition` 描述 DAG：

```python
from ..engine import EdgeDefinition, NodeDefinition, WorkflowDefinition
from ..types import NodeType

MY_WORKFLOW = WorkflowDefinition(
    nodes=[
        NodeDefinition(id="start", type=NodeType.START, data={...}),
        NodeDefinition(id="llm",   type=NodeType.LLM,   data={...}),
        NodeDefinition(id="end",   type=NodeType.END,   data={...}),
    ],
    edges=[
        EdgeDefinition(source="start", target="llm"),
        EdgeDefinition(source="llm",   target="end"),
    ],
)
```

然后在 `services/workflow_service.py` 中新增对应的触发函数即可。
