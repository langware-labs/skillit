"""Inject session_id into session record on SessionStart."""
from utils.conf import get_session_output_dir
from memory.rule_engine.trigger_executor import Action


def evaluate(hooks_data: dict, transcript: list) -> Action | None:
    hook_event = hooks_data.get("hookEvent", "")
    if hook_event != "SessionStart":
        return None

    session_id = hooks_data.get("session_id", "")
    if not session_id:
        return None

    from plugin_records.skillit_records import skillit_records
    from plugin_records.skillit_session import SkillitSession

    sessions = skillit_records.sessions
    sessions.load()
    session = sessions.get(session_id)
    if session is None:
        session = sessions.create(SkillitSession(session_id=session_id))
    sessions.save()

    session_output_dir = get_session_output_dir(session_id)

    context = (
        f"Session initialized.session_id={session_id}\n"
        f"The flow output directory is {session_output_dir}, "
        "remember to write to it when asked to use 'flow output dir'."
    )

    return Action(
        type="add_context",
        params={"content": context},
    )
