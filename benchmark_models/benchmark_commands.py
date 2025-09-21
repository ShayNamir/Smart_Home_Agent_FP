"""
Smart Home Agent Benchmark Commands
מכיל את כל הפקודות למבחן הביצועים של מודלים מקומיים
"""

from typing import List, Dict, Any

# רשימת המכשירים הזמינים במערכת
DEVICES = {
    "light": [
        "Bed Light",
        "Ceiling Lights", 
        "Kitchen Lights",
        "Office Lights",
        "Living Room Lights",
        "Entrance Lights",
    ],
    "switch": [
        "Decorative Lights",
    ],
    "lock": [
        "Front Door",
        "Kitchen Door", 
        "Openable Lock",
    ],
    "fan": [
        "Living Room Fan",
        "Ceiling Fan",
        "Percentage Full Fan",
        "Percentage Limited Fan",
        "Preset Only Limited Fan",
    ],
}

# פקודות פעולה (action commands)
ACTION_COMMANDS = [
    # פקודות הדלקה
    "turn on the bed light",
    "switch on the ceiling lights",
    "activate the kitchen lights",
    "please turn on the office lights",
    "can you turn on the living room lights",
    "power on the entrance lights",
    "enable the decorative lights",
    
    # פקודות כיבוי
    "turn off the bed light",
    "switch off the ceiling lights", 
    "deactivate the kitchen lights",
    "please turn off the office lights",
    "can you turn off the living room lights",
    "power off the entrance lights",
    "disable the decorative lights",
    
    # פקודות מאווררים
    "turn on the living room fan",
    "start the ceiling fan",
    "activate the percentage full fan",
    "please turn on the percentage limited fan",
    "can you start the preset only limited fan",
    "turn off the living room fan",
    "stop the ceiling fan",
    "deactivate the percentage full fan",
    "please turn off the percentage limited fan",
    "can you stop the preset only limited fan",
    
    # פקודות נעילה
    "lock the front door",
    "please lock the kitchen door",
    "secure the openable lock",
    "unlock the front door",
    "please unlock the kitchen door",
    "open the openable lock",
]

# פקודות סטטוס (status queries)
STATUS_COMMANDS = [
    # בדיקת מצב תאורה
    "what is the state of the bed light",
    "what's the status of the ceiling lights",
    "is the kitchen lights on",
    "is the office lights off",
    "check the living room lights status",
    "tell me the current state of the entrance lights",
    "what is the status of the decorative lights",
    
    # בדיקת מצב מאווררים
    "what is the state of the living room fan",
    "what's the status of the ceiling fan",
    "is the percentage full fan on",
    "is the percentage limited fan off",
    "check the preset only limited fan status",
    
    # בדיקת מצב נעילות
    "is the front door locked",
    "is the kitchen door unlocked",
    "what is the status of the openable lock",
    "check if the front door is secure",
    "is the kitchen door open",
]

# פקודות שגיאה (error handling)
ERROR_COMMANDS = [
    # מכשירים שלא קיימים
    "turn on the garden light",
    "switch off the hallway lamp",
    "activate the balcony lights",
    "please power on the garage light",
    "unlock the back gate",
    "lock the safe room door",
    "turn on the bathroom fan",
    "stop the attic fan",
    
    # פקודות מעורפלות
    "turn it on",
    "turn it off",
    "switch that one on",
    "please activate",
    "do the thing",
    "make it work",
    "change the setting",
]

def get_all_commands() -> List[str]:
    """מחזיר את כל הפקודות למבחן"""
    return ACTION_COMMANDS + STATUS_COMMANDS + ERROR_COMMANDS

def get_commands_by_category(category: str) -> List[str]:
    """מחזיר פקודות לפי קטגוריה"""
    if category == "action_commands":
        return ACTION_COMMANDS
    elif category == "status_queries":
        return STATUS_COMMANDS
    elif category == "error_handling":
        return ERROR_COMMANDS
    else:
        return []

def get_command_categories() -> List[str]:
    """מחזיר את כל הקטגוריות"""
    return ["action_commands", "status_queries", "error_handling"]

def get_category_weight(category: str) -> int:
    """מחזיר משקל לקטגוריה"""
    weights = {
        "action_commands": 3,
        "status_queries": 2, 
        "error_handling": 1
    }
    return weights.get(category, 1)

def get_short_test_commands() -> List[str]:
    """מחזיר פקודות למבחן קצר (כ-20 פקודות)"""
    short_commands = []
    
    # 8 פקודות פעולה
    short_commands.extend(ACTION_COMMANDS[:8])
    
    # 8 פקודות סטטוס
    short_commands.extend(STATUS_COMMANDS[:8])
    
    # 4 פקודות שגיאה
    short_commands.extend(ERROR_COMMANDS[:4])
    
    return short_commands

def get_long_test_commands() -> List[str]:
    """מחזיר את כל הפקודות למבחן ארוך"""
    return get_all_commands()

if __name__ == "__main__":
    print(f"פקודות פעולה: {len(ACTION_COMMANDS)}")
    print(f"פקודות סטטוס: {len(STATUS_COMMANDS)}")
    print(f"פקודות שגיאה: {len(ERROR_COMMANDS)}")
    print(f"סה\"כ פקודות: {len(get_all_commands())}")
    print(f"פקודות למבחן קצר: {len(get_short_test_commands())}")
