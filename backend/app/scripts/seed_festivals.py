import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import engine, SessionLocal, Base
from app.models.entities import FolkFestival

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    existing_count = db.query(FolkFestival).count()
    if existing_count > 0:
        print(f"FolkFestival table already has {existing_count} records. Skipping seed.")
        db.close()
        return

    festivals = [
        FolkFestival(
            title="杨柳青元宵灯会与年画展",
            solar_date="2026-03-03",
            lunar_date="正月十五",
            category="PAINTING",
            tag="津门元宵特辑",
            customs="赏经典彩灯、套印明清木版年画、打灯谜、吃元宵",
            description="杨柳青古镇素有“户户会点染，家家善丹青”之美誉。元宵佳节，古镇张灯结彩，展出经典木版套印画样，乡村小学师生可实地研学采风与拓印体验。",
            cover_url="/static/images/painting_1.svg",
            status="PUBLISHED",
            sort_order=1
        ),
        FolkFestival(
            title="海河端午龙舟竞渡非遗展演",
            solar_date="2026-06-19",
            lunar_date="五月初五",
            category="FOLK_CUSTOM",
            tag="水上非遗盛会",
            customs="海河龙舟赛、品天津小枣粽、佩香囊、绘雄黄",
            description="海河水系孕育了津派独特的水上龙舟竞渡文化。组织乡村学生手工制作传统龙舟模型，观摩海河非遗展演，体味团结协作与坚韧不拔的津沽精气神。",
            cover_url="/static/images/shadow_puppet_1.svg",
            status="PUBLISHED",
            sort_order=2
        ),
        FolkFestival(
            title="津门中秋拜月与兔子王泥塑节",
            solar_date="2026-09-25",
            lunar_date="八月十五",
            category="CLAY",
            tag="津沽民俗专题",
            customs="供兔子王泥塑、品天津白皮月饼、赏海河明月、诵诗词",
            description="天津旧俗八月十五中秋节，家家户户供奉“泥人张兔子王”，神态生动、盔甲鲜明。乡村课堂带领孩子们用彩泥亲手揉塑兔子王，寄托团圆安康的美好心愿。",
            cover_url="/static/images/clay_1.svg",
            status="PUBLISHED",
            sort_order=3
        ),
        FolkFestival(
            title="蓟州盘山重阳登高与民俗茱萸会",
            solar_date="2026-10-18",
            lunar_date="九月初九",
            category="FOLK_CUSTOM",
            tag="秋日茱萸雅集",
            customs="登盘山古道、插茱萸、品重阳花糕、敬老采风",
            description="蓟州盘山重阳登高风习历史悠久。组织乡村学子探访秋色长城与古寺，品尝特色五彩重阳糕，开展敬老尊贤传统美育实践。",
            cover_url="/static/images/kite_1.svg",
            status="PUBLISHED",
            sort_order=4
        ),
        FolkFestival(
            title="小年祭灶与天津独流焖糖民俗",
            solar_date="2027-02-08",
            lunar_date="腊月廿三",
            category="FOLK_CUSTOM",
            tag="岁末迎春非遗",
            customs="供糖瓜祭灶王、剪窗花、贴杨柳青年画",
            description="“二十三，糖瓜粘，灶君老爷要上天”。天津静海独流焖糖技艺传承数百年，酥脆香甜，课堂联动民间剪纸与年画，揭开津门浓郁年味的序幕。",
            cover_url="/static/images/shadow_puppet_1.svg",
            status="PUBLISHED",
            sort_order=5
        ),
    ]

    for f in festivals:
        db.add(f)
    db.commit()
    print(f"Successfully seeded {len(festivals)} FolkFestival records.")
    db.close()

if __name__ == "__main__":
    seed()
