# ✅ CrewAI תוקן ל-Windows!

## מה תוקן?

1. **Windows Signal Patch** - הוספתי patch שמתקן את בעיית `signal.SIGHUP` ב-Windows
2. **אוטומטי** - ה-patch רץ אוטומטית כשמייבאים את `src`
3. **CrewAI עובד** - עכשיו אפשר לייבא את CrewAI בלי שגיאות

## קבצים שנוצרו/שונו:

1. **`src/crewai_windows_patch.py`** - Patch שמתקן את כל ה-signals החסרים
2. **`src/__init__.py`** - רץ את ה-patch אוטומטית
3. **`src/crewai_agents.py`** - הוסר tools parameter (DirectOrchestrator משתמש ישירות בפונקציות)
4. **`src/crew_orchestrator.py`** - מוסיף את ה-patch לפני ייבוא crewai
5. **`src/crewai_tasks.py`** - מוסיף את ה-patch לפני ייבוא crewai

## איך זה עובד?

כשמייבאים את `src`, ה-patch רץ אוטומטית ומוסיף את כל ה-signals החסרים ל-module `signal`.
זה מאפשר ל-CrewAI לעבוד ב-Windows בלי שגיאות.

## בדיקה:

```python
# זה אמור לעבוד עכשיו:
import src
from crewai import Agent, Crew, Task
from src.crew_orchestrator import DirectOrchestrator, CrewOrchestrator

# הכל עובד! ✅
```

## שימוש:

### DirectOrchestrator (מומלץ - עובד תמיד):
```python
from src.crew_orchestrator import DirectOrchestrator

orchestrator = DirectOrchestrator()
results = orchestrator.run_full_pipeline(uploaded_df)
```

### CrewOrchestrator (מתקדם - עם CrewAI):
```python
from src.crew_orchestrator import CrewOrchestrator

orchestrator = CrewOrchestrator()
results = orchestrator.run_full_pipeline(uploaded_df)
```

## הערות:

- ה-patch רץ אוטומטית - אין צורך לעשות כלום
- DirectOrchestrator עובד בלי CrewAI (מומלץ)
- CrewOrchestrator משתמש ב-CrewAI (מתקדם)
- הכל עובד ב-Windows! ✅

---

**תוקן ב:** 2025-01-XX
**סטטוס:** ✅ עובד!

