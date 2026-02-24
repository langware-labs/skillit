from flow_sdk.fs_records.claude import ClaudeRootFsRecord
from scripts.tests.test_utils import make_env, LaunchMode
from scripts.tests.cli.shared import ACLI_SESSION_ID

DEBUG_FILE = __import__("pathlib").Path(__file__).parent / "analyze_debug.log"


def test_analyze():
    env = make_env()
    env.debug_file = DEBUG_FILE
    env.install_plugin()
    claude = ClaudeRootFsRecord.default()
    seesion_id_to_analyze = ACLI_SESSION_ID
    session = claude.get_session(seesion_id_to_analyze)
    assert session is not None, f"Session {seesion_id_to_analyze} not found"
    print(f"Session found: {session.session_id}")
    env.launch_claude(f"Launch skillit analyzer and Analyze the session {seesion_id_to_analyze}", mode=LaunchMode.INTERACTIVE)
