"""LLM 调用指标收集 + 会话级 Trace

Priority 1: 全局 token / latency 统计
Priority 2: session_id 串联 trace，面试结束输出完整链路日志

用法：
    from app.common.metrics import get_global_metrics, start_session_trace

    # 启动面试时
    start_session_trace(session_id)

    # 面试结束时
    finish_session_trace()

    # 查看全局指标
    stats = get_global_metrics()
"""

import logging
import time
import traceback
from contextvars import ContextVar
from dataclasses import dataclass, field

log = logging.getLogger(__name__)

# ========== ContextVar：当前会话 ID ==========

_active_session_id: ContextVar[str | None] = ContextVar("active_session_id", default=None)


# ========== 数据结构 ==========

@dataclass
class LLMCallRecord:
    """单次 LLM 调用记录"""
    caller: str            # 调用来源（模块.函数）
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class SessionTrace:
    """会话级 Trace —— 记录一次面试中所有 LLM 调用"""
    session_id: str
    calls: list[LLMCallRecord] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)

    def add_call(self, record: LLMCallRecord):
        self.calls.append(record)

    def summary(self) -> dict:
        """生成 Trace 摘要"""
        if not self.calls:
            return {"session_id": self.session_id, "total_calls": 0}

        total_prompt = sum(c.prompt_tokens for c in self.calls)
        total_completion = sum(c.completion_tokens for c in self.calls)
        total_tokens = sum(c.total_tokens for c in self.calls)
        total_latency = sum(c.latency_ms for c in self.calls)
        elapsed = (time.time() - self.start_time) * 1000

        # 按调用方分组
        by_caller: dict[str, list[LLMCallRecord]] = {}
        for c in self.calls:
            by_caller.setdefault(c.caller, []).append(c)

        caller_stats = []
        for caller, records in by_caller.items():
            caller_stats.append({
                "caller": caller,
                "calls": len(records),
                "tokens": sum(r.total_tokens for r in records),
                "latency_ms": round(sum(r.latency_ms for r in records), 1),
            })

        return {
            "session_id": self.session_id,
            "total_calls": len(self.calls),
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens": total_tokens,
            "total_latency_ms": round(total_latency, 1),
            "elapsed_ms": round(elapsed, 1),
            "by_caller": caller_stats,
        }

    def log_summary(self):
        """以结构化日志输出 Trace 摘要"""
        s = self.summary()
        if s["total_calls"] == 0:
            log.info("[trace:%s] 面试结束，无 LLM 调用", self.session_id)
            return

        log.info(
            "[trace:%s] ====== 面试 Trace 摘要 ======\n"
            "  LLM 调用: %d 次 | 总耗时: %.1fs | Wall-clock: %.1fs\n"
            "  Prompt: %d tokens | Completion: %d tokens | 总计: %d tokens",
            self.session_id,
            s["total_calls"],
            s["total_latency_ms"] / 1000,
            s["elapsed_ms"] / 1000,
            s["total_prompt_tokens"],
            s["total_completion_tokens"],
            s["total_tokens"],
        )

        for cs in s["by_caller"]:
            log.info(
                "[trace:%s]   %-45s  %2d 次  %6d tokens  %6.1fs",
                self.session_id,
                cs["caller"],
                cs["calls"],
                cs["tokens"],
                cs["latency_ms"] / 1000,
            )


# ========== 全局指标累加器 ==========

class LLMMetrics:
    """全局 LLM 调用指标（线程安全，惰性初始化）"""

    def __init__(self):
        self.total_calls = 0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.total_latency_ms = 0.0
        self._by_model: dict[str, dict] = {}

    def record(self, r: LLMCallRecord):
        self.total_calls += 1
        self.total_prompt_tokens += r.prompt_tokens
        self.total_completion_tokens += r.completion_tokens
        self.total_tokens += r.total_tokens
        self.total_latency_ms += r.latency_ms

        m = self._by_model.setdefault(r.model, {
            "calls": 0, "tokens": 0, "latency_ms": 0.0,
        })
        m["calls"] += 1
        m["tokens"] += r.total_tokens
        m["latency_ms"] += r.latency_ms

    def snapshot(self) -> dict:
        return {
            "total_calls": self.total_calls,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "total_latency_s": round(self.total_latency_ms / 1000, 2),
            "by_model": dict(self._by_model),
        }


_global_metrics = LLMMetrics()
_active_traces: dict[str, SessionTrace] = {}


# ========== 对外接口 ==========

def record_call(record: LLMCallRecord):
    """记录一次 LLM 调用（由 llm_client 调用）"""
    _global_metrics.record(record)

    session_id = _active_session_id.get()
    if session_id and session_id in _active_traces:
        _active_traces[session_id].add_call(record)


def start_session_trace(session_id: str):
    """启动会话 Trace（面试开始时调用）"""
    _active_traces[session_id] = SessionTrace(session_id=session_id)
    _active_session_id.set(session_id)
    log.info("[trace:%s] Trace 已启动", session_id)


def finish_session_trace(session_id: str | None = None) -> SessionTrace | None:
    """结束会话 Trace 并输出摘要（面试结束时调用）"""
    sid = session_id or _active_session_id.get()
    if not sid or sid not in _active_traces:
        return None

    trace = _active_traces.pop(sid)
    trace.log_summary()

    if _active_session_id.get() == sid:
        _active_session_id.set(None)

    return trace


def get_global_metrics() -> dict:
    """获取全局 LLM 调用指标"""
    return _global_metrics.snapshot()


def get_active_trace(session_id: str | None = None) -> SessionTrace | None:
    """获取当前活跃的 SessionTrace"""
    sid = session_id or _active_session_id.get()
    return _active_traces.get(sid) if sid else None


def _detect_caller() -> str:
    """从调用栈中识别 LLM 调用来源"""
    for frame in traceback.extract_stack():
        fn = frame.filename
        if "llm_client" in fn or "metrics" in fn:
            continue
        if "app" in fn:
            name = fn.split("app")[-1].lstrip("\\/").replace("\\", ".").replace("/", ".").removesuffix(".py")
            return f"{name}:{frame.name}"
    return "unknown"
