from enum import StrEnum
from collections.abc import Sequence

# Selector 是变量的地址，固定两个元素：[node_id, var_name]
# Dify 同样固定长度为 2，但同时支持 3+ 元素用于嵌套访问（如 FileSegment 的属性）
# 我们暂时只支持标准的两层寻址，嵌套访问未来有需要再加
Selector = Sequence[str]


class SegmentType(StrEnum):
    """变量的值类型枚举。

    Dify 在此基础上还有 SECRET（脱敏字符串）和 ARRAY_* 细分类型
    （ARRAY_STRING / ARRAY_NUMBER / ARRAY_FILE / ARRAY_BOOLEAN / ARRAY_ANY）。
    我们将所有数组统一为 ARRAY，SECRET 暂时省略，
    保留核心的 7 种类型，足以覆盖节点间数据传递的绝大多数场景。
    """

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    NONE = "none"


# 系统变量的命名空间节点 ID，对应 Dify 的 SYSTEM_VARIABLE_NODE_ID 常量
# Dify 还有 ENVIRONMENT_VARIABLE_NODE_ID / CONVERSATION_VARIABLE_NODE_ID 等命名空间
# 我们先只保留 sys，其余命名空间未来按需扩展
SYS_NODE_ID = "sys"


class NodeType(StrEnum):
    """节点类型枚举，引擎通过它把 workflow 定义中的字符串路由到对应的节点类。

    Dify 的节点类型远多于此（CODE / TEMPLATE_TRANSFORM / ITERATION /
    PARAMETER_EXTRACTOR / KNOWLEDGE_RETRIEVAL 等），
    我们只保留当前用得到的核心类型，未来按需扩展。
    """

    START = "start"
    END = "end"
    LLM = "llm"
    ARTIFACT_LOADER = "artifact_loader"
    ARTIFACT_SAVER = "artifact_saver"
