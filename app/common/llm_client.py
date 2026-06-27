"""LLM 调用封装

封装与大语言模型交互的所有方法：
1. chat_completion()           — 普通聊天，返回文本
2. chat_completion_json()      — 聊天 + 自动解析 JSON
3. chat_completion_with_tools() — 聊天 + function calling（Agent 核心）
4. chat_completion_stream()    — 流式聊天

底层使用 OpenAI 兼容 API，可对接 DeepSeek / DashScope / Ollama 等。
"""

import json
import logging
import re
import time

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessage

from app.common.metrics import LLMCallRecord, _detect_caller, record_call
from app.config import settings

log = logging.getLogger(__name__)

# ========== 客户端（模块级单例）==========

chat_client = AsyncOpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
)

embedding_client = AsyncOpenAI(
    base_url=settings.embedding_base_url,
    api_key=settings.embedding_api_key,
)


# ========== 普通聊天 ==========

async def chat_completion(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.7,
    history: list[dict] | None = None,
    max_tokens: int = 8192,
) -> str:
    """调用 LLM，返回完整文本"""
    used_model = model or settings.llm_model
    log.info("LLM 调用: model=%s, temp=%.1f, max_tokens=%d", used_model, temperature, max_tokens)

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_prompt})

    t0 = time.monotonic()
    resp = await chat_client.chat.completions.create(
        model=used_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    latency_ms = (time.monotonic() - t0) * 1000

    result = resp.choices[0].message.content or ""
    usage = resp.usage
    total_tokens = usage.total_tokens if usage else 0
    log.info("LLM 响应: model=%s, tokens=%d, len=%d, latency=%.0fms",
             used_model, total_tokens, len(result), latency_ms)

    # 记录指标
    record_call(LLMCallRecord(
        caller=_detect_caller(),
        model=used_model,
        prompt_tokens=usage.prompt_tokens if usage else 0,
        completion_tokens=usage.completion_tokens if usage else 0,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
    ))

    return result


# ========== 工具调用（Agent 核心）==========

async def chat_completion_with_tools(
    system_prompt: str,
    user_prompt: str,
    tools: list[dict] | None = None,
    tool_choice: str = "auto",
    model: str | None = None,
    temperature: float = 0.7,
    history: list[dict] | None = None,
    max_tokens: int = 8192,
) -> ChatCompletionMessage:
    """调用 LLM 并支持 function calling

    与 chat_completion 的区别：
    - 支持 tools 参数（OpenAI function calling 格式）
    - 返回 ChatCompletionMessage 对象（而非仅字符串）
    - 调用方通过 response.tool_calls 判断是否触发工具

    当 tools 为空时，行为等同于 chat_completion（但返回 Message 对象）。
    """
    used_model = model or settings.llm_model
    log.info("LLM 工具调用: model=%s, tools=%d", used_model, len(tools) if tools else 0)

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_prompt})

    kwargs = {
        "model": used_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice

    t0 = time.monotonic()
    resp = await chat_client.chat.completions.create(**kwargs)
    latency_ms = (time.monotonic() - t0) * 1000
    message = resp.choices[0].message

    usage = resp.usage
    total_tokens = usage.total_tokens if usage else 0
    log.info("LLM 工具响应: model=%s, tokens=%d, tool_calls=%d, latency=%.0fms",
             used_model, total_tokens,
             len(message.tool_calls) if message.tool_calls else 0, latency_ms)

    # 记录指标
    record_call(LLMCallRecord(
        caller=_detect_caller(),
        model=used_model,
        prompt_tokens=usage.prompt_tokens if usage else 0,
        completion_tokens=usage.completion_tokens if usage else 0,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
    ))

    return message


# ========== JSON 提取 ==========

def _extract_json_text(raw: str) -> str:
    """从 LLM 响应中提取 JSON 文本（去 <think> / markdown 代码块）"""
    text = raw.strip()
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    if text.startswith("```"):
        lines = text.split("\n")
        end_idx = len(lines)
        for i in range(len(lines) - 1, 0, -1):
            if lines[i].strip() == "```":
                end_idx = i
                break
        text = "\n".join(lines[1:end_idx]).strip()
    return text


async def chat_completion_json(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 8192,
) -> dict:
    """调用 LLM 并解析 JSON 响应"""
    text = await chat_completion(system_prompt, user_prompt, model, temperature, max_tokens=max_tokens)
    extracted = _extract_json_text(text)

    try:
        return json.loads(extracted)
    except json.JSONDecodeError as e:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        raise ValueError(f"LLM 响应无法解析为 JSON: {text[:300]}") from e


# ========== 流式聊天 ==========

async def chat_completion_stream(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.7,
    history: list[dict] | None = None,
):
    """流式调用 LLM，逐块 yield 文本片段"""
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_prompt})

    stream = await chat_client.chat.completions.create(
        model=model or settings.llm_model,
        messages=messages,
        temperature=temperature,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content


# ========== Embedding ==========

async def get_embedding(text: str) -> list[float]:
    """获取单个文本的嵌入向量"""
    resp = await embedding_client.embeddings.create(
        model=settings.embedding_model,
        input=text,
    )
    return resp.data[0].embedding


async def get_embeddings(texts: list[str]) -> list[list[float]]:
    """批量获取嵌入向量"""
    resp = await embedding_client.embeddings.create(
        model=settings.embedding_model,
        input=texts,
    )
    return [item.embedding for item in resp.data]
