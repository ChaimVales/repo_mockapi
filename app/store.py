# In-memory store for user metadata.
# Keyed by user_personal_number.
# This is a mock — data is not persisted between server restarts.

user_contexts: dict[str, dict] = {}

# היסטוריית שיחות - לכל user_personal_number יש רשימה של שיחותיו.
# כל פריט: {"session_id": "...", "summary": "..."}
# נוקה ב-restart של השרת. בעתיד יוחלף ב-DB אמיתי.
conversation_history: dict[str, list[dict]] = {}

# הודעות שמורות - לכל user יש dict של {session_id: [messages]}
# כל הודעה: {"message_id", "sender" ("user"/"bot"), "text", "timestamp"}
conversation_messages: dict[str, dict[str, list[dict]]] = {}

# מספר מקסימלי של שיחות שנשמרות בהיסטוריה לכל משתמש.
# שיחות מעבר למספר הזה - נמחקות אוטומטית (החדשות נשמרות, הישנות יוצאות).
MAX_HISTORY_ITEMS = 30


def add_conversation_to_history(user_id: str, session_id: str, summary: str) -> None:
    """
    מוסיף שיחה חדשה לראש ההיסטוריה של המשתמש.
    אם זו שיחה ראשונה - יוצר רשימה חדשה.
    אם ה-session_id כבר קיים - לא מוסיף שוב.
    אם הרשימה עוברת את MAX_HISTORY_ITEMS - מוחקים את הישנים ביותר.
    """
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    # מניעת כפילויות - אם session_id כבר ברשימה, לא מוסיפים שוב
    existing_ids = {c["session_id"] for c in conversation_history[user_id]}
    if session_id in existing_ids:
        return

    # מוסיפים בראש - שיחה חדשה מופיעה למעלה
    conversation_history[user_id].insert(0, {
        "session_id": session_id,
        "summary": summary,
    })

    # אכיפת המקסימום - חותכים את הישנים מהסוף
    if len(conversation_history[user_id]) > MAX_HISTORY_ITEMS:
        # מוצאים אילו session_id-ים נמחקים, כדי לנקות גם את ההודעות שלהם
        kept = conversation_history[user_id][:MAX_HISTORY_ITEMS]
        removed_ids = {
            c["session_id"]
            for c in conversation_history[user_id][MAX_HISTORY_ITEMS:]
        }
        conversation_history[user_id] = kept
        # ניקוי הודעות של שיחות שנמחקו
        if user_id in conversation_messages:
            for sid in removed_ids:
                conversation_messages[user_id].pop(sid, None)


def add_message_to_conversation(
    user_id: str,
    session_id: str,
    message_id: str,
    sender: str,                  # "user" / "bot"
    text: str,
    timestamp: str,
) -> None:
    """
    מוסיף הודעה לרשימת ההודעות של שיחה מסוימת.
    הודעות נשמרות בסדר כרונולוגי - בסוף הרשימה.
    """
    if user_id not in conversation_messages:
        conversation_messages[user_id] = {}
    if session_id not in conversation_messages[user_id]:
        conversation_messages[user_id][session_id] = []
    conversation_messages[user_id][session_id].append({
        "message_id": message_id,
        "sender": sender,
        "text": text,
        "timestamp": timestamp,
    })


def get_conversation_messages(user_id: str, session_id: str) -> list[dict]:
    """מחזיר את כל ההודעות של שיחה מסוימת (ריק אם לא קיימת)"""
    return conversation_messages.get(user_id, {}).get(session_id, [])


def get_conversation_summary(user_id: str, session_id: str) -> str | None:
    """מחזיר את ה-summary של שיחה לפי session_id (None אם לא קיים)"""
    for conv in conversation_history.get(user_id, []):
        if conv["session_id"] == session_id:
            return conv["summary"]
    return None
