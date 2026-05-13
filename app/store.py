# In-memory store for user metadata.
# Keyed by user_personal_number.
# This is a mock — data is not persisted between server restarts.

user_contexts: dict[str, dict] = {}

# היסטוריית שיחות - לכל user_personal_number יש רשימה של שיחותיו.
# כל פריט: {"session_id": "...", "summary": "..."}
# נוקה ב-restart של השרת. בעתיד יוחלף ב-DB אמיתי.
conversation_history: dict[str, list[dict]] = {}


def add_conversation_to_history(user_id: str, session_id: str, summary: str) -> None:
    """
    מוסיף שיחה חדשה לראש ההיסטוריה של המשתמש.
    אם זו שיחה ראשונה - יוצר רשימה חדשה.
    אם ה-session_id כבר קיים - לא מוסיף שוב.
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
