"""Prompt 模板加载器

使用 Jinja2 加载和渲染 prompt 模板。
模板文件位于 app/modules/interview/prompts/templates/ 目录下。
"""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

log = logging.getLogger(__name__)

# 模板目录
_TEMPLATE_DIR = Path(__file__).parent.parent / "modules" / "interview" / "prompts" / "templates"
_env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), trim_blocks=True, lstrip_blocks=True)


def render_prompt(template_name: str, **kwargs) -> str:
    """渲染 prompt 模板

    Args:
        template_name: 模板文件名（如 "agent_system.j2"）
        **kwargs: 模板变量

    Returns:
        渲染后的 prompt 字符串
    """
    try:
        template = _env.get_template(template_name)
        return template.render(**kwargs)
    except Exception as e:
        log.error("模板加载失败: %s, error=%s", template_name, e)
        return ""
