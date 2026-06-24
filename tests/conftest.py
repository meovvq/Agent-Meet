"""Pytest 配置文件"""

import asyncio
from typing import AsyncGenerator

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """创建全局事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
