from fastapi import APIRouter, Header, HTTPException

from app.models.schemas import (
    ConversationDetail,
    ConversationMessage,
    ConversationSummary,
    HistoryResponse,
)
from app.store import (
    MAX_HISTORY_ITEMS,
    conversation_history,
    get_conversation_messages,
    get_conversation_summary,
)

router = APIRouter()


"""
history - endpoint לקבלת רשימת שיחות קודמות של המשתמש (תקצירים בלבד)
"""
@router.get("/history", response_model=HistoryResponse)
async def get_history(
    api_key: str = Header(...),
    user_personal_number: str = Header(...),
) -> HistoryResponse:
    # שולף את השיחות של המשתמש מה-storage. ריק אם אין.
    # מגביל לראשי הרשימה - 30 השיחות החדשות ביותר.
    user_conversations = conversation_history.get(user_personal_number, [])[:MAX_HISTORY_ITEMS]

    return HistoryResponse(
        user_personal_number=user_personal_number,
        conversations=[
            ConversationSummary(**c) for c in user_conversations
        ],
    )


"""
history/conversation - endpoint להחזרת תוכן שיחה מסוימת לפי session_id
שולח את כל ההודעות (משתמש + בוט) של השיחה.
משמש את הסיידבר לפתיחת שיחה היסטורית במצב read-only.

@param session_id - query parameter (כדי לעקוף בעיות URL encoding של תווים מיוחדים)
@returns ConversationDetail - {session_id, summary, messages[]}
"""
@router.get("/history/conversation", response_model=ConversationDetail)
async def get_conversation(
    session_id: str,                                # query parameter: ?session_id=...
    api_key: str = Header(...),
    user_personal_number: str = Header(...),
) -> ConversationDetail:
    summary = get_conversation_summary(user_personal_number, session_id)
    if summary is None:
        # השיחה לא קיימת אצל המשתמש - 404
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = get_conversation_messages(user_personal_number, session_id)

    return ConversationDetail(
        session_id=session_id,
        summary=summary,
        messages=[ConversationMessage(**m) for m in messages],
    )
