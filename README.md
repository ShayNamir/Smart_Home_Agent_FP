# Smart Home Agent Final Project

פרויקט גמר - סוכן בית חכם מבוסס AI עם השוואת ארכיטקטורות ומודלים

## תיאור הפרויקט

פרויקט זה מפתח סוכן בית חכם המבוסס על מודלי AI מקומיים (Ollama) ומשווה בין ארכיטקטורות שונות לביצוע משימות בית חכם. הפרויקט כולל:

- **סוכן בית חכם** עם תמיכה במודלים מקומיים
- **השוואת ארכיטקטורות** (Standard, CoT, ReAct, Reflexion, ToT)
- **השוואת מודלים** מקומיים
- **בנצ'מארק מקיף** עם דוחות Excel מפורטים

## מבנה הפרויקט

```
Smart_Home_Agent_FP/
├── agent_runner.py          # רכיב ראשי להרצת הסוכן
├── main.py                  # קובץ ראשי להרצת הפרויקט
├── core/                    # רכיבי ליבה
│   ├── ha.py               # ממשק Home Assistant
│   └── objects.py          # אובייקטים בסיסיים
├── src/smart_home_agent/    # קוד מקור
│   └── architectures/      # ארכיטקטורות AI
├── bench/                   # בנצ'מארק ארכיטקטורות
│   ├── arch_benchmark.py   # השוואת ארכיטקטורות
│   └── model_benchmark.py  # השוואת מודלים
├── benchmark_models/        # בנצ'מארק מודלים חדש
│   ├── benchmark_runner.py  # הרצת בנצ'מארק מודלים
│   └── benchmark_commands.py # פקודות בנצ'מארק
├── config/                  # קבצי תצורה
├── docs/                    # תיעוד
└── scripts/                 # סקריפטים עזר
```

## התקנה

### דרישות מערכת

- Python 3.8+
- Home Assistant (מותקן ומריץ)
- Ollama עם מודלים מקומיים

### התקנת תלויות

```bash
pip install -r config/requirements.txt
```

### התקנת מודלים ב-Ollama

```bash
# התקנת מודלים מומלצים
ollama pull phi3:mini
ollama pull llama3.2
ollama pull mistral
ollama pull qwen3:4b
ollama pull gemma3:4b
ollama pull deepseek-r1:1.5b
```

## שימוש

### הרצת הסוכן הראשי

```bash
python main.py
```

### בנצ'מארק ארכיטקטורות

```bash
cd bench
python arch_benchmark.py
```

### בנצ'מארק מודלים

```bash
cd benchmark_models
python benchmark_runner.py
```

## ארכיטקטורות נתמכות

1. **Standard** - ארכיטקטורה בסיסית
2. **CoT** - Chain of Thought
3. **ReAct** - Reasoning and Acting
4. **Reflexion** - Self-reflection
5. **ToT** - Tree of Thoughts

## מודלים נתמכים

- phi3:mini
- llama3.2
- mistral
- qwen3:4b
- gemma3:4b
- deepseek-r1:1.5b

## קטגוריות פקודות

- **פקודות פעולה** - הדלקה/כיבוי מכשירים
- **שאילתות סטטוס** - בדיקת מצב מכשירים
- **טיפול בשגיאות** - פקודות למכשירים לא קיימים

## פלט

הפרויקט יוצר דוחות Excel מפורטים עם:

- השוואת ביצועים בין ארכיטקטורות
- השוואת ביצועים בין מודלים
- ניתוח לפי קטגוריות פקודות
- סטטיסטיקות זמן ביצוע

## תרומה לפרויקט

1. Fork את הפרויקט
2. צור branch חדש (`git checkout -b feature/AmazingFeature`)
3. Commit את השינויים (`git commit -m 'Add some AmazingFeature'`)
4. Push ל-branch (`git push origin feature/AmazingFeature`)
5. פתח Pull Request

## רישיון

פרויקט זה מופץ תחת רישיון MIT. ראה קובץ `LICENSE` לפרטים נוספים.

## קשר

- מחבר: [שם המחבר]
- אימייל: [כתובת אימייל]
- פרויקט: [קישור לפרויקט]

## הודעות תודה

תודה לכל התורמים והקהילה שעזרו בפיתוח הפרויקט הזה.
