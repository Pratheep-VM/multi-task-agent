import importlib


def test_modular_multiagent_exports():
    modules = [
        "app.tools.website_api_tools",
        "app.tools.research_tools",
        "app.tools.coder_tools",
        "app.agents.supervisor",
        "app.agents.research_agent",
        "app.agents.coder_agent",
        "app.agents.website_api_agent",
        "app.workflows.multiagent_graph",
    ]

    for module_name in modules:
        module = importlib.import_module(module_name)
        assert module is not None

    tool_module = importlib.import_module("app.tools.agent_tools")
    assert hasattr(tool_module, "RESEARCH_TOOLS")
    assert hasattr(tool_module, "CODER_TOOLS")
    assert hasattr(tool_module, "WEBSITE_TOOLS")

    graph_module = importlib.import_module("app.workflows.multiagent_graph")
    assert hasattr(graph_module, "multi_agent_system")
