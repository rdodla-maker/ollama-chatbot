import importlib.util
from pathlib import Path


# Load the router module directly from its file to avoid package import issues
_router_path = Path(__file__).resolve().parent.parent / "backend" / "agent" / "router.py"
spec = importlib.util.spec_from_file_location("router", str(_router_path))
router = importlib.util.module_from_spec(spec)
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
spec.loader.exec_module(router)


def test_decide_tool_parsing(monkeypatch):
    # Stub the module-level llm to avoid touching Pydantic model attributes
    class DummyLLM:
        def invoke(self, prompt):
            return '{"tool":"calculator","args":{"expression":"2+2"}}'

    monkeypatch.setattr(router, "llm", DummyLLM())

    res = router.decide_tool("What is 2+2?")

    assert isinstance(res, dict)
    assert res.get("tool") == "calculator"
    assert res.get("args", {}).get("expression") == "2+2"
