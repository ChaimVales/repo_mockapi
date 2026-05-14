from fastapi import APIRouter, Header

from app.models.schemas import FeedbackRequest

router = APIRouter()


"""
feedback - endpoint לקבלת משוב משתמש על תשובת בוט
מקבל סנטימנט (חיובי/שלילי), סיבה אופציונלית מרשימה סגורה, וטקסט חופשי
לכשהמשתמש בוחר "אחר".

**הראוט מטפל גם בשינוי משוב** - אם המשתמש שינה Like ל-Dislike או להפך,
הלקוח שולח POST חדש עם הסנטימנט המעודכן. במצב Mock פשוט מדפיסים ל-log.
בפרודקשן: ה-DB צריך לעשות UPSERT לפי (user, message_id) - לעדכן אם קיים.

@param body - אובייקט FeedbackRequest עם פרטי המשוב
@returns 204 No Content (אישור התקבל, ללא תוכן)
"""
@router.post("/feedback", status_code=204)
async def feedback(
    body: FeedbackRequest,
    api_key: str = Header(...),
    user_personal_number: str = Header(...),
) -> None:
    # רישום המשוב ב-log של השרת (יוצג ב-uvicorn console)
    # בעתיד: שמירה ב-DB, שליחה לאנליטיקס, ניתוח לשיפור המודל
    print(
        f"[FEEDBACK] user={user_personal_number} | "
        f"session={body.session_id} | "
        f"sentiment={body.sentiment} | "
        f"reason={body.reason or '(none)'} | "
        f"free_text={body.free_text or '(none)'}"
    )
