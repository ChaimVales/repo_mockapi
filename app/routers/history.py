from fastapi import APIRouter, Header

from app.models.schemas import ConversationSummary, HistoryResponse
from app.store import conversation_history

router = APIRouter()


"""
history - endpoint לקבלת רשימת שיחות קודמות של המשתמש
מחזיר אובייקט HistoryResponse עם user_personal_number ורשימת conversations.
הרשימה מתעדכנת אוטומטית בכל פעם שמשתמש מתחיל שיחה חדשה דרך /chat/stream.

@param api_key - מפתח API לאימות
@param user_personal_number - מזהה המשתמש - הרשימה מסוננת לפיו
@returns HistoryResponse - {user_personal_number, conversations[]}
"""
@router.get("/history", response_model=HistoryResponse)
async def get_history(
    api_key: str = Header(...),
    user_personal_number: str = Header(...),
) -> HistoryResponse:
    # שולף את השיחות של המשתמש מה-storage. ריק אם אין.
    user_conversations = conversation_history.get(user_personal_number, [])

    return HistoryResponse(
        user_personal_number=user_personal_number,
        conversations=[
            ConversationSummary(**c) for c in user_conversations
        ],
    )
