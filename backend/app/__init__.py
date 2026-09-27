"""
Career-OS backend application package.

This is the top-level Python package for the FastAPI backend. All application
subpackages (agents, api, core, models) are rooted here so that absolute imports
like ``from app.agents.graph import pipeline_app`` resolve correctly regardless
of the working directory used to launch the server.
"""
