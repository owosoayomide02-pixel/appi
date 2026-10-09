from pathlib import Path
import importlib.util


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_android_placeholder_does_not_fake_success():
    root = Path(__file__).resolve().parents[3]
    mod = _load(root / "apps" / "runtimes" / "android" / "main.py")
    result = mod.execute("contacts.read", {})
    assert result["success"] is False
    assert result["error_code"] == "CAPABILITY_UNAVAILABLE"
    assert result["platform"] == "android"


def test_ios_placeholder_does_not_fake_success():
    root = Path(__file__).resolve().parents[3]
    mod = _load(root / "apps" / "runtimes" / "ios" / "main.py")
    result = mod.execute("calendar.write", {})
    assert result["success"] is False
    assert result["error_code"] == "CAPABILITY_UNAVAILABLE"
