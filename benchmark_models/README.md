# Smart Home Agent Model Benchmark

חבילה להשוואת ביצועים של מודלים מקומיים עבור Smart Home Agent.

## תיאור

חבילה זו מאפשרת להשוות את הביצועים של מודלים מקומיים שונים (Ollama) במשימות של Smart Home Agent. הבנצ'מארק בודק את יכולת המודלים לבצע פקודות פעולה, לענות על שאילתות סטטוס ולטפל בשגיאות.

## תכונות

- **מבחן קצר**: כ-20 פקודות נבחרות לבדיקה מהירה
- **מבחן ארוך**: כל הפקודות הזמינות לבדיקה מקיפה
- **השוואת מודלים**: בדיקת מספר מודלים במקביל
- **דוח Excel**: יצירת דוח מפורט עם נוסחאות
- **תמיכה בעברית**: ממשק משתמש בעברית

## מודלים נתמכים

- phi3:mini
- llama3.2
- mistral
- qwen3:4b
- gemma3:4b
- deepseek-r1:1.5b

## קטגוריות פקודות

1. **פקודות פעולה** (Action Commands): הדלקה/כיבוי מכשירים, נעילה/פתיחה
2. **שאילתות סטטוס** (Status Queries): בדיקת מצב מכשירים
3. **טיפול בשגיאות** (Error Handling): פקודות למכשירים לא קיימים או מעורפלים

## שימוש

### הרצה ישירה

```bash
cd benchmark_models
python benchmark_runner.py
```

### שימוש כמודול

```python
from benchmark_models import run_model_benchmark

# מבחן קצר עם כל המודלים
run_model_benchmark("short")

# מבחן ארוך עם מודלים נבחרים
run_model_benchmark("long", ["phi3:mini", "llama3.2"])
```

### שימוש מתקדם

```python
from benchmark_models import ModelBenchmarkRunner

runner = ModelBenchmarkRunner(iterations=5)
results = runner.run_benchmark("short", ["phi3:mini"])
excel_file = runner.generate_excel_report()
```

## פלט

הבנצ'מארק יוצר:

1. **דוח Excel** (`smart_home_model_benchmark_YYYYMMDD_HHMM.xlsx`) עם:
   - גיליון "All Results": כל התוצאות
   - גיליון "Summary": סיכום כללי
   - גיליון "Model Comparison": השוואת מודלים
   - גיליון "Category Analysis": ניתוח לפי קטגוריות

2. **קובץ JSON** (`model_benchmark_results_YYYYMMDD_HHMM.json`) עם התוצאות הגולמיות

## דרישות

- Python 3.8+
- pandas
- openpyxl
- pydantic-ai
- Home Assistant API

## התקנה

```bash
pip install pandas openpyxl pydantic-ai
```

## הערות

- הבנצ'מארק דורש חיבור פעיל ל-Home Assistant
- מומלץ להריץ את המבחן הקצר קודם לבדיקת תקינות המערכת
- התוצאות נשמרות בתיקיית `benchmark_results`
