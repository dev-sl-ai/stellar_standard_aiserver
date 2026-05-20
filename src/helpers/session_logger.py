import os
from pathlib import Path
from src.helpers.maps import BUTTON_TITLE_MAP

def write_user_session_log(ctx):
    """
    Write a clean log file with session info and chat memory.
    """
    if not ctx.session_id:
        return  # No active session

    desktop_path = Path.home() / "Desktop"
    user_log_dir = desktop_path / "AIアバターSTELLAデモ版" / "logs" / "user"

    os.makedirs(user_log_dir, exist_ok=True)

    log_file = user_log_dir / f"{ctx.session_id}.log"

    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"セッションID  : {ctx.session_id}\n")
        f.write(f"開始時刻  : {ctx.session_start_time}\n")
        f.write(f"終了時刻  : {ctx.session_end_time or '進行中'}\n")
        f.write(f"選択したボタン    : {BUTTON_TITLE_MAP.get(ctx.button_id,"")}\n")
        f.write(f"選択したボタン    : 一般会話\n")
        f.write("\n会話ログ :\n")

        previous_line = ""

        for line in ctx.get_memory():
            if "来訪者:" in line and "アバター:" in line:
                parts = line.split("アバター:")
                user = parts[0].replace("来訪者:", "").strip().rstrip(",")
                avatar = parts[1].strip()

                if user:
                    user_line = f"来訪者: {user}"
                    if user_line != previous_line:
                        f.write(user_line + "\n")
                        previous_line = user_line

                if avatar:
                    avatar_line = f"アバター: {avatar}"
                    if avatar_line != previous_line:
                        f.write(avatar_line + "\n")
                        previous_line = avatar_line


                
