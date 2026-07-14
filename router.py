from commands import (
    apps,
    system,
    browser,
    file,
    developer,
    communication,
    productivity,
    automation,
    smart,
    utilities,

)

"""
=========================================================
Arya V2.0
Command Router
=========================================================
"""

from typing import Dict, Callable
import traceback
import time

# ================================
# Import Command Modules
# ================================

from commands.apps import (
    open_app,
    close_app,
)

from commands.browser import (
    google_search,
    youtube_search,
    open_website,
)

from commands.system import (
    shutdown,
    restart,
    lock_pc,
    take_screenshot,
)

from commands.file import (
    create_folder,
    delete_file,
)

from commands.media import (
    play_music,
    pause_music,
    volume_up,
    volume_down,
    mute_volume,
    send_whatsapp,
)

from commands.communication import (
    send_email,
    open_telegram,
    open_meet,
    arrange_a_meeting_on_meet,
    open_zoom,
)

from ai.gemini import ai_chat

# =====================================
# Intent Mapping
# =====================================

ROUTES: Dict[str, Callable] = {

    # ---------------- Apps ----------------
    "open_app": open_app,
    "close_app": close_app,

    # ---------------- Browser ----------------
    "google_search": google_search,
    "youtube_search": youtube_search,
    "open_website": open_website,

    # ---------------- System ----------------
    "shutdown": shutdown,
    "restart": restart,
    "lock_pc": lock_pc,
    "screenshot": take_screenshot,

    # ---------------- Files ----------------
    "create_folder": create_folder,
    "delete_file": delete_file,

    # ---------------- Media ----------------
    "play_music": play_music,
    "pause_music": pause_music,
    "volume_up": volume_up,
    "volume_down": volume_down,
    "mute_volume": mute_volume,
    "send_whatsapp": send_whatsapp,

    # ---------------- Communication ----------------
    "send_email": send_email,
    "open_telegram": open_telegram,
    "open_meet": open_meet,
    "arrange_meeting": arrange_a_meeting_on_meet,
    "open_zoom": open_zoom,

    # ---------------- AI ----------------
    "chat": ai_chat,
}


# =====================================
# Execute Intent
# =====================================

def execute(intent: str, params: dict = None):

    """
    Execute an intent returned by Gemini.

    Args:
        intent : Intent name
        params : Parameters dictionary

    Returns:
        Dictionary
    """

    start = time.time()

    if params is None:
        params = {}

    print("=" * 60)
    print(f"Intent : {intent}")
    print(f"Params : {params}")
    print("=" * 60)

    if intent not in ROUTES:

        return {

            "success": False,

            "intent": intent,

            "message": f"No handler found for '{intent}'."

        }

    function = ROUTES[intent]

    try:
        result = function(**params)

        execution_time = round(time.time() - start, 3)

        if isinstance(result, dict):

            result["execution_time"] = execution_time

            result["intent"] = intent

            return result

        return {

            "success": True,

            "intent": intent,

            "message": str(result),

            "execution_time": execution_time

        }

    except TypeError as e:

        return {

            "success": False,

            "intent": intent,

            "message": f"Parameter Error : {e}"

        }

    except Exception as e:

        traceback.print_exc()

        return {

            "success": False,

            "intent": intent,

            "message": str(e)

        }
