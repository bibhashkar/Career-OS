"""
FastAPI router modules for REST and WebSocket endpoints.

This package is the transport layer of Career-OS. Each module mounts one
logical API surface (CV generation, job search, feedback, interview coaching)
and delegates immediately to the compiled LangGraph application instances.
No business logic lives here — routers are thin adapters between HTTP/WS
requests and the agent layer.
"""
