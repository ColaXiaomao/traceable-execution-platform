"""路由器配置分析 workflow 定义。

这是一个固定在工单业务里的具体 workflow：
  1. StartNode     — 接收 artifact_id（用户上传的路由器配置文件 ID）
  2. ArtifactLoader — 从存储层读取配置文件的文本内容
  3. LLMNode       — 把配置文本发给 LLM，输出安全性评价报告
  4. ArtifactSaver  — 把评价报告保存为新的 artifact，与工单永久关联
  5. EndNode       — 返回评价文本 + 新 artifact ID 给调用方

为什么把 workflow 定义写成代码而不是存数据库？
- 当前阶段 workflow 数量少，代码定义改起来更快，版本管理更清晰
- 存数据库适合用户在 UI 上动态编辑 workflow 的场景（Dify 的做法）
- 未来如果需要用户自定义 workflow，再迁移到 DB 存储即可
"""

from ..engine import EdgeDefinition, NodeDefinition, WorkflowDefinition
from ..types import NodeType

ROUTER_CONFIG_ANALYSIS: WorkflowDefinition = WorkflowDefinition(
    nodes=[
        NodeDefinition(
            id="start",
            type=NodeType.START,
            data={
                "input_schema": [
                    {"variable": "artifact_id", "required": True},
                ]
            },
        ),
        NodeDefinition(
            id="load_config",
            type=NodeType.ARTIFACT_LOADER,
            data={
                "artifact_selector": ["start", "artifact_id"],
                "encoding": "utf-8",
            },
        ),
        NodeDefinition(
            id="llm_analyze",
            type=NodeType.LLM,
            data={
                "model": "local-mistral",
                "system_prompt": (
                    "你是一名网络安全专家，擅长分析路由器配置文件。"
                    "请从安全性、规范性、最佳实践三个维度给出专业评价，指出具体问题和改进建议。"
                ),
                "prompt_template": (
                    "请分析以下路由器配置文件（文件名：{{load_config.filename}}），"
                    "给出详细的安全评价报告：\n\n{{load_config.content}}"
                ),
            },
        ),
        NodeDefinition(
            id="save_analysis",
            type=NodeType.ARTIFACT_SAVER,
            data={
                "content_selector": ["llm_analyze", "response"],
                "filename": "router_analysis_report.txt",
                "artifact_type": "llm_analysis",
                "description": "LLM 自动生成的路由器配置安全评价报告",
            },
        ),
        NodeDefinition(
            id="end",
            type=NodeType.END,
            data={
                "outputs": [
                    {"name": "analysis",            "selector": ["llm_analyze", "response"]},
                    {"name": "analysis_artifact_id","selector": ["save_analysis", "artifact_id"]},
                    {"name": "config_filename",     "selector": ["load_config", "filename"]},
                ]
            },
        ),
    ],
    edges=[
        EdgeDefinition(source="start",       target="load_config"),
        EdgeDefinition(source="load_config",  target="llm_analyze"),
        EdgeDefinition(source="llm_analyze",  target="save_analysis"),
        EdgeDefinition(source="save_analysis",target="end"),
    ],
)
