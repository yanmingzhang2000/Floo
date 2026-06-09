"""初始化盲盒角色数据 - 执行一次即可。"""
from app.database import SessionLocal
from app.models import Character

CHARACTERS = [
    # 普通（common）- 权重 7000（70%）
    {"name": "Wisdom", "meaning": "智慧", "rarity": "common", "weight": 7000, "description": "洞察世事的智慧"},
    {"name": "Courage", "meaning": "勇气", "rarity": "common", "weight": 7000, "description": "无畏前行的勇气"},
    {"name": "Hope", "meaning": "希望", "rarity": "common", "weight": 7000, "description": "照亮前路的希望"},
    {"name": "Faith", "meaning": "信念", "rarity": "common", "weight": 7000, "description": "坚定不移的信念"},
    {"name": "Grace", "meaning": "优雅", "rarity": "common", "weight": 7000, "description": "从容优雅的姿态"},
    {"name": "Peace", "meaning": "和平", "rarity": "common", "weight": 7000, "description": "内心宁静的平和"},
    {"name": "Love", "meaning": "爱", "rarity": "common", "weight": 7000, "description": "温暖万物的爱"},
    # 稀有（rare）- 权重 2500（25%）
    {"name": "Serenity", "meaning": "宁静", "rarity": "rare", "weight": 2500, "description": "深邃如海的宁静"},
    {"name": "Brilliance", "meaning": "才华", "rarity": "rare", "weight": 2500, "description": "璀璨夺目的才华"},
    # 传说（legendary）- 权重 500（5%）
    {"name": "Infinity", "meaning": "无限", "rarity": "legendary", "weight": 500, "description": "无限可能的传说"},
]

def init_characters():
    db = SessionLocal()
    try:
        for char_data in CHARACTERS:
            existing = db.query(Character).filter(Character.name == char_data["name"]).first()
            if not existing:
                char = Character(**char_data)
                db.add(char)
        db.commit()
        print(f"✅ 初始化完成，共 {len(CHARACTERS)} 个角色")
    except Exception as e:
        db.rollback()
        print(f"❌ 出错: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_characters()
