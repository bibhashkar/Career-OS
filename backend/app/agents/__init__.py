"""
LangGraph multi-agent orchestration package.

Contains the shared state schema (state.py), compiled graph factory functions
(graph.py), individual agent node implementations (nodes/), and external tool
integrations (tools/). The agents package is the core intelligence layer of
Career-OS — all LLM calls, routing logic, and workflow orchestration live here,
keeping the API layer a thin transport boundary.
"""
