"""Inject session_id into session record on SessionStart."""
from memory.rule_engine.trigger_executor import Action
from utils.log import skill_log


def evaluate(hooks_data: dict, transcript: list) -> Action | None:
    hook_event = hooks_data.get("hookEvent", "")
    if hook_event != "SessionStart":
        return None

    session_id = hooks_data.get("session_id", "")
    if not session_id:
        return None

    from plugin_records.skillit_records import skillit_records
    session = skillit_records.create_session(session_id)
    skill_log(f"[System context Rule]: session={session_id},output dir: {session.output_dir}")
    context = (
        f"Session initialized.session_id={session_id}\n"
        f"The flow output directory is {session.output_dir}, "
        "remember to write to it when asked to use 'flow output dir'."
    )

    return Action(
        type="add_context",
        params={"content": context},
    )
