from pathlib import Path
from levelupdiag_core.manifest import load_manifest


def test_universe_quick_is_static_and_fast():
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(root)
    assert manifest["campaigns"]["universe-quick"]["levels"] == ["N00", "N01", "N11"]


def test_host_command_env_composes_worlds_backend(tmp_path, monkeypatch):
    import os
    from levelupdiag_core.config import AppConfig
    from konnaxion_diag.common import _command_env

    diag = tmp_path / "LevelUpDiag"
    host = tmp_path / "Konnaxion"
    worlds = tmp_path / "Konnaxion_Worlds"
    (host / "backend").mkdir(parents=True)
    (host / "frontend").mkdir(parents=True)
    (worlds / "backend" / "konnaxion" / "worlds").mkdir(parents=True)
    diag.mkdir(parents=True)

    cfg = AppConfig({
        "target_repo_root": str(host),
        "konnaxion": {
            "backend_dir": "backend",
            "frontend_dir": "frontend",
            "worlds": {"repo_dir": "../Konnaxion_Worlds"},
        },
        "env": {"PYTHONPATH": "existing-path"},
    }, diag)

    env = _command_env(cfg, host / "backend")
    parts = env["PYTHONPATH"].split(os.pathsep)
    assert parts[0] == str((worlds / "backend").resolve())
    assert "existing-path" in parts


def test_worlds_command_env_does_not_add_host_composition(tmp_path):
    from levelupdiag_core.config import AppConfig
    from konnaxion_diag.common import _command_env

    diag = tmp_path / "LevelUpDiag"
    host = tmp_path / "Konnaxion"
    worlds = tmp_path / "Konnaxion_Worlds"
    (host / "backend").mkdir(parents=True)
    (host / "frontend").mkdir(parents=True)
    (worlds / "backend" / "konnaxion" / "worlds").mkdir(parents=True)
    diag.mkdir(parents=True)

    cfg = AppConfig({
        "target_repo_root": str(host),
        "konnaxion": {
            "backend_dir": "backend",
            "frontend_dir": "frontend",
            "worlds": {"repo_dir": "../Konnaxion_Worlds"},
        },
        "env": {"PYTHONPATH": "keep-me"},
    }, diag)

    env = _command_env(cfg, worlds / "backend")
    assert env["PYTHONPATH"] == "keep-me"

