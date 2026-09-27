"""
Agent node function implementations.

Each module in this package exports a single async node function that reads
from AgentState, performs its unit of work (job search, CV tailoring, ATS
scoring, interview simulation, etc.), and returns a partial state update dict.
Nodes are composable and stateless between invocations — all continuity lives
in the LangGraph checkpoint stored by PostgresSaver or MemorySaver.
"""
