from fastapi import APIRouter, Header   # APIRouter לקיבוץ endpoints, Header לקבלת HTTP headers

from app.models.schemas import InitRequest   # מודל ה-Pydantic לולידציה של ה-body
from app.store import user_contexts          # storage גלובלי (dict בזיכרון) של הקשרי משתמשים

# יצירת router שיקבץ את ה-endpoints. יחובר לאפליקציה הראשית עם app.include_router()
router = APIRouter()


"""
init - endpoint לאיתחול הקשר של משתמש
מתקבל בקריאה הראשונה מהלקוח כשהאפליקציה עולה.
שומר את ההקשר העסקי של המשתמש (יחידה, תפקיד, תוכנית וכו') ב-storage,
כדי שבבקשות הבאות (/chat) השרת ידע באיזה הקשר המשתמש פועל.

@param body - אובייקט InitRequest עם פרטי ההקשר. FastAPI מאמת אוטומטית
@param api_key - מפתח API לאימות. מגיע מה-HTTP header 'api-key'
@param user_personal_number - מזהה ייחודי של המשתמש. מגיע מ-header 'user-personal-number'
@returns None - תגובה ריקה עם status 204 (No Content)
"""
@router.post("/init", status_code=204)   # רישום ה-endpoint: POST /init, מחזיר 204 (הצלחה ללא תוכן)
async def init(
    body: InitRequest,                          # body מסוג InitRequest. FastAPI מאמת ומפרש את ה-JSON אוטומטית
    api_key: str = Header(...),                 # header 'api-key' (FastAPI ממיר _ ל-). הסימן ... אומר חובה
    user_personal_number: str = Header(...),    # header 'user-personal-number'. מזהה את המשתמש
) -> None:
    # ממיר את ה-Pydantic model חזרה ל-dict רגיל ושומר ב-storage תחת מזהה המשתמש
    # בבקשות הבאות (/chat) הקוד יוכל לקרוא מכאן את ההקשר של המשתמש
    user_contexts[user_personal_number] = body.model_dump()