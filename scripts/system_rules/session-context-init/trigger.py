"""Inject session_id into session record on SessionStart."""

from pathlib import Path

from memory.rule_engine.trigger_executor import Action
from plugin_records.skillit_records import skillit_records
from utils.log import skill_log


def evaluate(hooks_data: dict, transcript: list) -> Action | None:
    hook_event = hooks_data.get("hookEvent", "")
    if hook_event != "SessionStart":
        return None

    session_id = hooks_data.get("session_id", "")
    if not session_id:
        return None

    session = skillit_records.create_session(session_id)
    skillit_home = str(Path(__file__).resolve().parents[3])
    flow_output_directory = str(session.output_dir)
    skill_log(f"[System context Rule]: session={session_id}, flow_output_directory dir: {flow_output_directory}")

    context = (
        "Session initialized.\n"
        f"session_id={session_id}\n"
        f"skillit_home={skillit_home}\n"
        f"flow_output_directory={flow_output_directory}\n"
        "Remember to write to <flow_output_directory> above when asked to use 'flow output dir'.\n"
    )

    return Action(
        type="add_context",
        params={"content": context},
    )
