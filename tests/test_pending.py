import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from services import pending_changes


def test_propose_approve(monkeypatch, tmp_path):
    root = tmp_path

    def fake_resolve(user_path: str) -> Path:
        name = Path(user_path).name
        return root / name

    monkeypatch.setattr(
        "services.pending_changes.resolve_safe_path",
        fake_resolve,
    )

    pending_changes._store.clear()
    target = root / "sample.txt"
    target.write_text("before", encoding="utf-8")

    msg = pending_changes.propose_file_edit("sample.txt", "after")
    assert "proposed" in msg.lower() or "Change" in msg

    items = pending_changes.list_pending()
    assert len(items) == 1
    change_id = items[0]["id"]

    pending_changes.approve_change(change_id)
    assert target.read_text(encoding="utf-8") == "after"


def test_reject(monkeypatch, tmp_path):
    root = tmp_path

    def fake_resolve(user_path: str) -> Path:
        return root / Path(user_path).name

    monkeypatch.setattr(
        "services.pending_changes.resolve_safe_path",
        fake_resolve,
    )

    pending_changes._store.clear()
    target = root / "keep.txt"
    target.write_text("original", encoding="utf-8")

    pending_changes.propose_file_edit("keep.txt", "changed")
    change_id = pending_changes.list_pending()[0]["id"]
    pending_changes.reject_change(change_id)
    assert target.read_text(encoding="utf-8") == "original"
    assert pending_changes.list_pending() == []
