"""Prompt 模板加载器

使用 Jinja2 加载和渲染 prompt 模板。
模板文件位于 app/modules/interview/prompts/templates/ 目录下。

使用 StrictUndefined：模板中引用了未传入的变量时，立即抛出 UndefinedError，
而不是静默渲染为空字符串。这能及早发现模板与代码的参数不一致。
"""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

log = logging.getLogger(__name__)

# 模板目录
_TEMPLATE_DIR = Path(__file__).parent.parent / "modules" / "interview" / "prompts" / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    undefined=StrictUndefined,    # 缺失变量立即报错，不静默为空
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_prompt(template_name: str, **kwargs) -> str:
    """渲染 prompt 模板

    Args:
        template_name: 模板文件名（如 "agent_system.j2"）
        **kwargs: 模板变量

    Returns:
        渲染后的 prompt 字符串

    Raises:
        UndefinedError: 模板中引用了未传入的变量
        TemplateNotFound: 模板文件不存在
    """
    template = _env.get_template(template_name)
    return template.render(**kwargs)
