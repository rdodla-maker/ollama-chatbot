import importlib.util
from pathlib import Path


# Load loop module directly to avoid package import resolution issues
_loop_path = Path(__file__).resolve().parent.parent / "backend" / "agent" / "loop.py"
spec = importlib.util.spec_from_file_location("loop", str(_loop_path))
loop = importlib.util.module_from_spec(spec)
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
spec.loader.exec_module(loop)


def test_run_agentic_loop_calculator(monkeypatch):
    # Prepare a sequence: first return a calculator action, then none to stop
    seq = [{"tool": "calculator", "args": {"expression": "2+2"}}, {"tool": "none", "args": {}}]

    def fake_decide(question):
        return seq.pop(0)

    monkeypatch.setattr(loop, "decide_tool", fake_decide)

    # Stub the module-level llm to avoid setting attributes on the Pydantic object
    class DummyLLM:
        def invoke(self, prompt):
            return "FINISH: 4"

    monkeypatch.setattr(loop, "llm", DummyLLM())

    # Replace memory_store with a lightweight dummy
    class DummyMemory:
        def __init__(self):
            self.entries = []

        def get_context_for_query(self, q):
            return ""

        def append(self, q, plan, resp):
            self.entries.append((q, plan, resp))

    monkeypatch.setattr(loop, "memory_store", DummyMemory())

    res = loop.run_agentic_loop("Calculate 2+2")

    assert isinstance(res, dict)
    assert "response" in res
    assert "4" in res["response"]
