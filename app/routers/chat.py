import asyncio                                  # מודול סטנדרטי לפעולות אסינכרוניות (sleep אסינכרוני)
import json                                     # להמרת dict ל-JSON לשליחה ב-SSE
from datetime import datetime                   # לפורמט session_id קריא: userId:timestamp

from fastapi import APIRouter, Header
from fastapi.responses import StreamingResponse  # להחזרת SSE (Server-Sent Events)

from app.mocks.scenarios import match_scenario   # פונקציה שמחזירה תרחישים מדומים לפי תוכן ההודעה (מחליף AI אמיתי בפיתוח)
from app.models.schemas import ChatRequest, ChatResponse   # מודלי Pydantic ל-input ו-output
from app.store import add_conversation_to_history  # להוספת שיחה חדשה להיסטוריית המשתמש

router = APIRouter()


# ============================================================
# הגדרות זמן - שנה כדי להתאים את הקצב
# ============================================================
# /chat (ראוט קלאסי, לא סטרימינג):
#   0 = תגובה מיידית, 3 = 3 שניות השהיה, וכו'
SIMULATED_DELAY_SECONDS = 8

# /chat/stream (ראוט חדש עם סטרימינג של actions):
#   זמן בין צעדי הסוכן (actions). 0.8 = ברירת מחדל מאוזנת.
ACTION_STEP_DELAY_SECONDS = 0.8

# אורך מקסימלי של summary בהיסטוריה (התווים הראשונים של ההודעה)
HISTORY_SUMMARY_MAX_LENGTH = 50


def _build_session_id(user_personal_number: str) -> str:
    """יוצר session_id בפורמט: user_id:YYYY-MM-DD-HHMMSS"""
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    return f"{user_personal_number}:{timestamp}"


def _build_summary(message: str) -> str:
    """יוצר תקציר קצר של השיחה מההודעה הראשונה"""
    if len(message) <= HISTORY_SUMMARY_MAX_LENGTH:
        return message
    return message[:HISTORY_SUMMARY_MAX_LENGTH].rstrip() + "..."


"""
chat - endpoint לטיפול בהודעות צ'אט מהמשתמש
מקבל הודעה, מייצר/משתמש במזהה סשן, מתאים תרחיש מדומה לפי ההודעה,
ובונה תגובה מובנית עם הטקסט, הישויות הגיאוגרפיות, ודגלי הבהרה.

response_model=ChatResponse מבטיח: ולידציה של התגובה, סינון שדות לא רצויים,
ותיעוד אוטומטי ב-Swagger.

@param body - אובייקט ChatRequest עם ההודעה ומזהה הסשן (אופציונלי)
@param api_key - מפתח API לאימות. מגיע מה-HTTP header 'api-key'
@param user_personal_number - מזהה המשתמש מ-header 'user-personal-number'
@returns ChatResponse - תגובת ה-AI, מזהה הסשן, וישויות גיאוגרפיות
"""
@router.post("/chat", response_model=ChatResponse)   # POST /chat, מחזיר 200 עם body מסוג ChatResponse
async def chat(
    body: ChatRequest,                          # body מסוג ChatRequest. FastAPI מאמת ומפרש את ה-JSON
    api_key: str = Header(...),                 # header חובה לאימות (כרגע לא נבדק - placeholder)
    user_personal_number: str = Header(...),    # מזהה המשתמש (כרגע לא משמש - placeholder לטעינת context)
) -> ChatResponse:
    # סימולציית זמן עיבוד של AI אמיתי - הסר/הקטן לפרודקשן
    if SIMULATED_DELAY_SECONDS > 0:
        await asyncio.sleep(SIMULATED_DELAY_SECONDS)

    # אם הלקוח לא שלח session_id (הודעה ראשונה) - יוצרים חדש בפורמט userId:timestamp
    # ומוסיפים אותו להיסטוריה של המשתמש
    is_new_session = not body.session_id
    session_id = body.session_id or _build_session_id(user_personal_number)
    if is_new_session:
        add_conversation_to_history(user_personal_number, session_id, _build_summary(body.message))

    # מתאים תרחיש מדומה לפי תוכן ההודעה (placeholder ל-AI אמיתי)
    scenario = match_scenario(body.message)

    # בונה את התגובה. שימוש ב-[] לשדות חובה ו-.get() לאופציונליים
    return ChatResponse(
        response=scenario["response"],                                          # טקסט התשובה - שדה חובה בתרחיש
        session_id=session_id,                                                  # מזהה השיחה (חדש או קיים)
        needs_clarification=scenario.get("needs_clarification", False),         # אופציונלי, ברירת מחדל False
        clarify_for=scenario.get("clarify_for"),                                # אופציונלי, ברירת מחדל None
        reasoning_content=None,                                                 # אין chain of thought במצב mock
        entities=scenario["entities"],                                          # ישויות גיאוגרפיות - שדה חובה בתרחיש
    )


# ============================================================
# /chat/stream - גרסה עם Server-Sent Events לסטרימינג של actions
# ============================================================
# המודל הזה מסמלץ סוכן AI אמיתי: שולח רצף של "פעולות" שהסוכן מבצע
# (כל אחת כ-event נפרד) ובסוף את התשובה הסופית.
#
# פורמט ה-events (תואם ל-OpenAI/Anthropic streaming):
#   {"type": "action", "text": "..."} - הסוכן מבצע פעולה
#   {"type": "response", "text": "...", "session_id": "...", "entities": [...]} - התשובה הסופית
#   [DONE] - סוף השידור
#
# בעתיד: כשתחבר LLM אמיתי, החלף את הלוגיקה כאן בקריאה ל-LLM streaming API
# והפרונטאנד לא יידע להבדיל - הפורמט נשאר זהה.
@router.post("/chat/stream")
async def chat_stream(
    body: ChatRequest,
    api_key: str = Header(...),
    user_personal_number: str = Header(...),
):
    # אם הלקוח לא שלח session_id - יוצרים חדש ומוסיפים להיסטוריה
    is_new_session = not body.session_id
    session_id = body.session_id or _build_session_id(user_personal_number)
    if is_new_session:
        add_conversation_to_history(user_personal_number, session_id, _build_summary(body.message))

    scenario = match_scenario(body.message)

    async def event_generator():
        """גנרטור אסינכרוני שמייצר event אחר event"""

        # 1. שולחים את הפעולות אחת אחר השנייה עם השהיה ביניהן
        for action_text in scenario.get("actions", []):
            event = {"type": "action", "text": action_text}
            # פורמט SSE: "data: <json>\n\n"
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            await asyncio.sleep(ACTION_STEP_DELAY_SECONDS)

        # 2. שולחים את התשובה הסופית
        response_event = {
            "type": "response",
            "text": scenario["response"],
            "session_id": session_id,
            "entities": [e.model_dump() for e in scenario["entities"]],
            "needs_clarification": scenario.get("needs_clarification", False),
            "clarify_for": scenario.get("clarify_for"),
        }
        yield f"data: {json.dumps(response_event, ensure_ascii=False)}\n\n"

        # 3. אות סוף (כמו OpenAI - לסימון שהשידור נגמר)
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",       # מונע caching של ה-stream
            "X-Accel-Buffering": "no",          # ל-nginx - לא לחסום את הסטרימינג
        },
    )
