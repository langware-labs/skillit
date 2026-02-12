"""Inject session_id into flow_context.json on SessionStart."""
from conf import get_session_output_dir
from memory.rule_engine.trigger_executor import Action


def evaluate(hooks_data: dict, transcript: list) -> Action | None:
    hook_event = hooks_data.get("hookEvent", "")
    if hook_event != "SessionStart":
        return None

    session_id = hooks_data.get("session_id", "")
    if not session_id:
        return None

    # Write session_id directly to the JSON store
    from conf import get_session_dir
    from mcp_server.json_store import jsonKeyVal

    session_dir = get_session_dir(session_id)
    store = jsonKeyVal(session_dir / "flow_context.json")
    store.set("session_id", session_id)
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
