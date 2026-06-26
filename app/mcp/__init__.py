"""Agent Meet MCP Server

通过 MCP 协议暴露面试工具，供外部 AI 客户端（Claude Desktop、Cursor 等）调用。

运行方式：
  stdio 模式（本地）：python -m app.mcp.server
  HTTP 模式（远程）：python -m app.mcp.server --transport streamable-http --port 8001
"""
