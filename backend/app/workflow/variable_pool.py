from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from .types import Selector, SYS_NODE_ID
from .variable import Variable, build_variable

# Dify 的模板语法是 {{#node_id.var_name#}}（带井号定界符），
# 我们用更通用的 {{node_id.var_name}}，去掉 # 降低阅读噪音。
_TEMPLATE_PATTERN = re.compile(r"\{\{([a-zA-Z0-9_]+\.[a-zA-Z0-9_]+)\}\}")

# Dify 的 SELECTORS_LENGTH 常量值为 2，强制 selector 只能两段。
# 我们同样只支持两段，但通过运行时校验而非常量，便于日后扩展。
_SELECTOR_LENGTH = 2


class VariablePool:
    """节点间共享数据的变量池，每次 workflow run 独享一个实例。

    内部结构：variable_dictionary[node_id][var_name] = Variable
    与 Dify 完全一致，两层字典保证 O(1) 读写。

    Dify 用 Pydantic BaseModel 是为了将 VariablePool 整体序列化到数据库
    （支持 workflow 暂停/恢复）。我们当前只做内存运行时，不需要序列化，
    用普通 Python 类更简洁。需要持久化时 snapshot() 方法已足够。

    Dify 的 VariablePool 还持有：
      - environment_variables（环境级别常量，跨 run 共享）
      - conversation_variables（对话上下文变量，多轮对话用）
      - rag_pipeline_variables（RAG 节点的输入变量）
    这三类变量与具体产品功能强绑定，我们暂时省略，未来按需加入。
    """

    def __init__(
        self,
        system_variables: dict[str, Any] | None = None,
        user_inputs: dict[str, Any] | None = None,
    ) -> None:
        # 两层字典：node_id → {var_name → Variable}
        self._store: defaultdict[str, dict[str, Variable]] = defaultdict(dict)
        # user_inputs 对应 Dify VariablePool.user_inputs 字段：
        # 存放本次 workflow run 的初始输入，StartNode 会读取这里并写入 start.* 命名空间。
        # Dify 把它作为 Pydantic 字段，我们直接存为普通属性即可。
        self.user_inputs: dict[str, Any] = user_inputs or {}
        if system_variables:
            for key, value in system_variables.items():
                self.add([SYS_NODE_ID, key], value)

    @classmethod
    def create(
        cls,
        system_variables: dict[str, Any] | None = None,
        user_inputs: dict[str, Any] | None = None,
    ) -> "VariablePool":
        """工厂方法，语义比直接 __init__ 更清晰，与 Dify 的 VariablePool.empty() 对应。"""
        return cls(system_variables=system_variables, user_inputs=user_inputs)

    # ------------------------------------------------------------------
    # 核心读写操作
    # ------------------------------------------------------------------

    def add(self, selector: Selector, value: Any) -> None:
        """向变量池写入变量。

        Dify 的 add() 接受 Variable / Segment / 原生值三种形式，
        通过 variable_factory 统一转换。
        我们接受 Variable 或原生值两种，去掉 Segment 中间层。
        """
        self._validate_selector(selector)
        node_id, var_name = selector[0], selector[1]

        variable = value if isinstance(value, Variable) else build_variable(selector, value)
        self._store[node_id][var_name] = variable

    def get(self, selector: Selector) -> Variable | None:
        """从变量池读取变量，不存在返回 None。

        Dify 的 get() 返回 Segment，并支持 3+ 段 selector 对
        FileSegment / ObjectSegment 做嵌套属性访问（如 file.url / obj.key）。
        我们暂时只支持标准两段寻址，嵌套访问留给未来扩展。
        """
        self._validate_selector(selector)
        node_id, var_name = selector[0], selector[1]
        return self._store.get(node_id, {}).get(var_name)

    def get_value(self, selector: Selector) -> Any:
        """直接返回变量的原始值，不存在返回 None。便于节点代码直接使用。"""
        var = self.get(selector)
        return var.value if var is not None else None

    def remove(self, selector: Selector) -> None:
        """删除变量。

        selector 长度为 1 时删除整个节点命名空间（节点重跑时清理旧输出用）。
        selector 长度为 2 时删除单个变量。
        与 Dify 行为一致。
        """
        if not selector:
            return
        if len(selector) == 1:
            self._store.pop(selector[0], None)
            return
        self._validate_selector(selector)
        node_id, var_name = selector[0], selector[1]
        self._store.get(node_id, {}).pop(var_name, None)

    # ------------------------------------------------------------------
    # 模板解析
    # ------------------------------------------------------------------

    def resolve_template(self, template: str) -> str:
        """将模板字符串中的 {{node_id.var_name}} 替换为实际值。

        Dify 的 convert_template() 返回 SegmentGroup（一组 Segment 的列表），
        用于在 LLM prompt 构建时保留每个片段的类型信息（比如区分文本和文件引用）。
        我们直接返回拼接好的字符串，因为当前节点只需要把值插入 prompt，
        不需要感知片段类型。
        """

        def _replace(match: re.Match) -> str:
            parts = match.group(1).split(".")
            var = self.get(parts)
            return var.text if var is not None else match.group(0)  # 找不到则原样保留

        return _TEMPLATE_PATTERN.sub(_replace, template)

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------

    def _validate_selector(self, selector: Selector) -> None:
        if len(selector) != _SELECTOR_LENGTH:
            raise ValueError(
                f"selector 必须是两段 [node_id, var_name]，收到 {len(selector)} 段：{list(selector)}"
            )

    def snapshot(self) -> dict[str, dict[str, Any]]:
        """导出所有变量的原始值，用于写入 Run.execution_context 做审计快照。

        Dify 没有对应方法，这是我们针对审计需求额外加的。
        """
        return {
            node_id: {var_name: var.value for var_name, var in vars_.items()}
            for node_id, vars_ in self._store.items()
        }
