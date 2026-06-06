#!/usr/bin/env python3
"""BaZi (八字) Calculator — Four Pillars of Destiny with Luck Cycle.

Usage:
    python bazi.py 1990 5 15 8 30   # year month day hour minute
    python bazi.py 1990 5 15 8 30 --gender male
    python bazi.py 1990 5 15 8 30 --gender male --json
"""

import argparse
import json
import sys
from datetime import date, datetime, timedelta

# =============================================================================
# Constants
# =============================================================================

HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
STEM_YINYANG = ["阳", "阴"]  # even index → yang, odd → yin
STEM_ELEMENT = ["木", "木", "火", "火", "土", "土", "金", "金", "水", "水"]
BRANCH_ELEMENT = ["水", "土", "木", "木", "土", "火", "火", "土", "金", "金", "土", "水"]

# Solar term names in Chinese
SOLAR_TERM_NAMES = [
    "小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨",
    "立夏", "小满", "芒种", "夏至", "小暑", "大暑", "立秋", "处暑",
    "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪", "冬至",
]

# The 12 Jie (节) that mark month boundaries: indices 2,4,...,22,0 in SOLAR_TERM_NAMES
# 立春(2), 惊蛰(4), 清明(6), 立夏(8), 芒种(10), 小暑(12),
# 立秋(14), 白露(16), 寒露(18), 立冬(20), 大雪(22), 小寒(0)
JIE_INDICES = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 0]

# Na Yin (纳音) table — 30 entries covering positions 0..29 of the sexagenary cycle
NAYIN = [
    "海中金", "炉中火", "大林木", "路旁土", "剑锋金",
    "山头火", "涧下水", "城头土", "白蜡金", "杨柳木",
    "泉中水", "屋上土", "霹雳火", "松柏木", "长流水",
    "沙中金", "山下火", "平地木", "壁上土", "金箔金",
    "覆灯火", "天河水", "大驿土", "钗钏金", "桑柘木",
    "大溪水", "沙中土", "天上火", "石榴木", "大海水",
]

# Na Yin descriptions — brief personality/life interpretation for each
NAYIN_DESCRIPTIONS = {
    "海中金": "金藏海底，内敛深沉，才华不轻易外露，需时机方能发光",
    "炉中火": "热情如火炉，性格鲜明有冲劲，做事积极但需注意耐心",
    "大林木": "如参天大树，根基深厚，性格稳重有担当，适合长期积累",
    "路旁土": "朴实如道旁之土，踏实稳重，默默耕耘，厚积薄发",
    "剑锋金": "锋芒如剑，锐利果断，有决断力，适合需要精确度的领域",
    "山头火": "如火在山头，光芒外显，性格外向有感染力，善交际",
    "涧下水": "如山涧溪流，灵动清秀，思维敏捷，适应力强",
    "城头土": "厚重如城墙，稳重可靠，有保护欲，适合管理岗位",
    "白蜡金": "精致如白蜡，细腻温和，有艺术气质，追求完美",
    "杨柳木": "柔韧如杨柳，随和善变通，人缘好但需坚定立场",
    "泉中水": "清澈如泉水，纯净透彻，心地善良，直觉敏锐",
    "屋上土": "稳固如屋基，安定踏实，重视家庭，有责任感",
    "霹雳火": "迅猛如霹雳，雷厉风行，爆发力强，适合开拓型工作",
    "松柏木": "坚毅如松柏，不屈不挠，耐压性强，越挫越勇",
    "长流水": "源远流长，持之以恒，有耐心耐力，适合长期项目",
    "沙中金": "金藏沙中，需淘洗方显，大器晚成，中年后运势渐显",
    "山下火": "火在山脚，温和持久，性格温暖不刺眼，人缘好",
    "平地木": "如平原之木，生长顺利，性格平和，人生较平稳",
    "壁上土": "坚如壁垒，意志坚定，有原则性，适合技术型工作",
    "金箔金": "华丽如金箔，外在光鲜，有审美品味，重形象",
    "覆灯火": "如灯中之火，照亮他人，有奉献精神，适合教育行业",
    "天河水": "浩瀚如天河，心胸开阔，志向远大，适合宏观思维的工作",
    "大驿土": "广阔如驿道，包容豁达，善于协调，适合公共服务",
    "钗钏金": "精巧如首饰，注重细节，心灵手巧，适合手工艺创作",
    "桑柘木": "实用如桑柘，朴实无华，务实重利，善于经营",
    "大溪水": "奔流如溪，活力充沛，行动力强，喜欢自由",
    "沙中土": "质朴如沙土，谦逊低调，不善张扬但内在丰富",
    "天上火": "炽热如天火，光芒万丈，有领导气质，气场强大",
    "石榴木": "坚韧如石榴，生命力强，多子多福，有韧性",
    "大海水": "包容如大海，胸襟广阔，格局大，适应力极强",
}

# Month branch → seasonal strength hint for each element
# 寅卯(春):木旺 巳午(夏):火旺 申酉(秋):金旺 亥子(冬):水旺 辰戌丑未(四季):土旺
MONTH_SEASON = {
    2: "春", 3: "春", 4: "春",   # 寅卯辰 → 春
    5: "夏", 6: "夏", 7: "夏",   # 巳午未 → 夏
    8: "秋", 9: "秋", 10: "秋",  # 申酉戌 → 秋
    11: "冬", 0: "冬", 1: "冬",  # 亥子丑 → 冬
}

# Which element is prosperous in each season
SEASON_PROSPEROUS = {"春": "木", "夏": "火", "秋": "金", "冬": "水"}

# Hidden Stems (藏干) for each Earthly Branch
# Format: list of (stem_index, strength) — first is primary (本气)
HIDDEN_STEMS = {
    0:  [(9, "本气")],                                          # 子 → 癸
    1:  [(5, "本气"), (9, "中气"), (7, "余气")],                # 丑 → 己 癸 辛
    2:  [(0, "本气"), (2, "中气"), (4, "余气")],                # 寅 → 甲 丙 戊
    3:  [(1, "本气")],                                          # 卯 → 乙
    4:  [(4, "本气"), (1, "中气"), (9, "余气")],                # 辰 → 戊 乙 癸
    5:  [(2, "本气"), (4, "中气"), (6, "余气")],                # 巳 → 丙 戊 庚
    6:  [(3, "本气"), (5, "本气")],                             # 午 → 丁 己
    7:  [(5, "本气"), (3, "中气"), (1, "余气")],                # 未 → 己 丁 乙
    8:  [(6, "本气"), (8, "中气"), (4, "余气")],                # 申 → 庚 壬 戊
    9:  [(7, "本气")],                                          # 酉 → 辛
    10: [(4, "本气"), (7, "中气"), (3, "余气")],                # 戌 → 戊 辛 丁
    11: [(8, "本气"), (0, "中气")],                             # 亥 → 壬 甲
}

# Hour to branch mapping (时辰)
# 子时 23:00-00:59, 丑时 01:00-02:59, ..., 亥时 21:00-22:59
HOUR_BRANCH_TABLE = [
    (23, 0), (1, 1), (3, 2), (5, 3), (7, 4), (9, 5),
    (11, 6), (13, 7), (15, 8), (17, 9), (19, 10), (21, 11),
]

# Month branch names for each month boundary (0-indexed — 寅月=0)
MONTH_BRANCH_NAMES = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]


# =============================================================================
# Solar Term Calculation
# =============================================================================

def _solar_term_c(year, term_index):
    """Return the C constant for a given solar term and year."""
    # C values for 20th century (1900-1999)
    c_20th = [
        6.11, 20.84, 4.87, 19.15, 6.42, 20.65, 5.59, 20.37,
        6.12, 21.29, 6.24, 21.59, 7.71, 23.14, 8.11, 23.36,
        8.49, 23.63, 9.04, 23.88, 8.27, 22.86, 7.72, 22.50,
    ]
    # C values for 21st century (2000-2099)
    c_21st = [
        5.4055, 20.12, 3.87, 18.73, 5.63, 20.646, 4.81, 20.1,
        5.52, 21.04, 5.678, 21.37, 7.108, 22.83, 7.5, 23.13,
        7.646, 23.042, 8.318, 23.438, 7.438, 22.36, 7.18, 21.94,
    ]
    if 1900 <= year <= 1999:
        return c_20th[term_index]
    elif 2000 <= year <= 2099:
        return c_21st[term_index]
    else:
        return c_21st[term_index]


def get_solar_term_date(year, term_index):
    """Get the approximate date of a solar term."""
    if term_index >= 12:
        y = year - 1900
    else:
        y = year - 1900

    c = _solar_term_c(year, term_index)
    day = int(c + 0.2422 * y - int(y / 4))

    month_map = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6,
                 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12]
    month = month_map[term_index]

    return month, day


def get_solar_terms_for_year(year):
    """Get all 24 solar term dates for a given year."""
    terms = []
    for i in range(24):
        month, day = get_solar_term_date(year, i)
        terms.append((month, day))
    return terms


def get_month_index_for_date(year, month, day):
    """Determine which month branch (0-11, starting with 寅=0) a date falls in."""
    terms = get_solar_terms_for_year(year)
    target = date(year, month, day)
    month_boundaries = []

    for i, jie_idx in enumerate(JIE_INDICES):
        m, d = terms[jie_idx]
        boundary_date = date(year, m, d)
        month_boundaries.append((i, boundary_date))

    sorted_boundaries = sorted(month_boundaries, key=lambda x: x[1])

    month_idx = None
    for mi, bd in reversed(sorted_boundaries):
        if target >= bd:
            month_idx = mi
            break

    if month_idx is None:
        month_idx = 11

    return month_idx


# =============================================================================
# Pillar Calculations
# =============================================================================

def calc_year_pillar(year):
    """Calculate year pillar (年柱)."""
    stem = HEAVENLY_STEMS[(year - 4) % 10]
    branch = EARTHLY_BRANCHES[(year - 4) % 12]
    return stem, branch, (year - 4) % 10, (year - 4) % 12


def calc_year_pillar_for_date(year, month, day):
    """Calculate year pillar considering 立春 boundary."""
    lichun_m, lichun_d = get_solar_term_date(year, 2)
    target = date(year, month, day)
    lichun = date(year, lichun_m, lichun_d)

    if target < lichun:
        year -= 1

    return calc_year_pillar(year)


def calc_month_pillar(year, month, day):
    """Calculate month pillar (月柱)."""
    month_idx = get_month_index_for_date(year, month, day)
    _, _, year_stem_idx, _ = calc_year_pillar_for_date(year, month, day)

    month_stem_idx = (year_stem_idx * 2 + month_idx) % 10
    month_branch_idx = (month_idx + 2) % 12

    return (
        HEAVENLY_STEMS[month_stem_idx],
        EARTHLY_BRANCHES[month_branch_idx],
        month_stem_idx,
        month_branch_idx,
    )


def day_number_from_1900(year, month, day):
    """Calculate the number of days since January 1, 1900."""
    target = date(year, month, day)
    reference = date(1900, 1, 1)
    return (target - reference).days


def calc_day_pillar(year, month, day):
    """Calculate day pillar (日柱). Reference: 1900-01-01 = 甲戌日 (stem=0, branch=10)"""
    delta = day_number_from_1900(year, month, day)
    stem_idx = delta % 10
    branch_idx = (delta + 10) % 12
    return HEAVENLY_STEMS[stem_idx], EARTHLY_BRANCHES[branch_idx], stem_idx, branch_idx


def calc_hour_pillar(day_stem_idx, hour, minute):
    """Calculate hour pillar (时柱)."""
    total_minutes = hour * 60 + minute

    if total_minutes >= 23 * 60 or total_minutes < 1 * 60:
        hour_branch_idx = 0
    elif total_minutes < 3 * 60:
        hour_branch_idx = 1
    elif total_minutes < 5 * 60:
        hour_branch_idx = 2
    elif total_minutes < 7 * 60:
        hour_branch_idx = 3
    elif total_minutes < 9 * 60:
        hour_branch_idx = 4
    elif total_minutes < 11 * 60:
        hour_branch_idx = 5
    elif total_minutes < 13 * 60:
        hour_branch_idx = 6
    elif total_minutes < 15 * 60:
        hour_branch_idx = 7
    elif total_minutes < 17 * 60:
        hour_branch_idx = 8
    elif total_minutes < 19 * 60:
        hour_branch_idx = 9
    elif total_minutes < 21 * 60:
        hour_branch_idx = 10
    else:
        hour_branch_idx = 11

    hour_stem_idx = (day_stem_idx * 2 + hour_branch_idx) % 10

    return (
        HEAVENLY_STEMS[hour_stem_idx],
        EARTHLY_BRANCHES[hour_branch_idx],
        hour_stem_idx,
        hour_branch_idx,
    )


# =============================================================================
# Sexagenary Cycle & Na Yin
# =============================================================================

def sexagenary_index(stem_idx, branch_idx):
    """Calculate the position (0-59) in the sexagenary cycle."""
    lookup = {}
    for n in range(60):
        s = n % 10
        b = n % 12
        lookup[(s, b)] = n
    return lookup[(stem_idx, branch_idx)]


def get_nayin(stem_idx, branch_idx):
    """Get Na Yin (纳音) for a pillar."""
    idx = sexagenary_index(stem_idx, branch_idx)
    return NAYIN[idx // 2]


# =============================================================================
# Hidden Stems
# =============================================================================

def get_hidden_stems(branch_idx):
    """Get hidden stems for an earthly branch."""
    return [(HEAVENLY_STEMS[s], strength) for s, strength in HIDDEN_STEMS[branch_idx]]


# =============================================================================
# Ten Gods (十神)
# =============================================================================

ELEMENT_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
ELEMENT_GENERATED_BY = {"火": "木", "土": "火", "金": "土", "水": "金", "木": "水"}
ELEMENT_CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
ELEMENT_CONTROLLED_BY = {"土": "木", "水": "土", "火": "水", "金": "火", "木": "金"}


def get_ten_god(day_stem_idx, target_stem_idx):
    """Calculate ten god (十神) relationship."""
    if day_stem_idx == target_stem_idx:
        return "比肩"

    day_elem = STEM_ELEMENT[day_stem_idx]
    target_elem = STEM_ELEMENT[target_stem_idx]
    day_yy = day_stem_idx % 2
    target_yy = target_stem_idx % 2
    same_yy = (day_yy == target_yy)

    if day_elem == target_elem:
        return "比肩" if same_yy else "劫财"
    elif ELEMENT_GENERATES[day_elem] == target_elem:
        return "食神" if same_yy else "伤官"
    elif ELEMENT_GENERATED_BY[day_elem] == target_elem:
        return "偏印" if same_yy else "正印"
    elif ELEMENT_CONTROLS[day_elem] == target_elem:
        return "偏财" if same_yy else "正财"
    elif ELEMENT_CONTROLLED_BY[day_elem] == target_elem:
        return "七杀" if same_yy else "正官"

    return "未知"


# =============================================================================
# BaZi Analysis Helpers
# =============================================================================

def count_ten_gods(pillars, day_stem_idx):
    """Count ten god appearances across all four pillars (surface stems only)."""
    counts = {}
    for p in pillars:
        if p["name"] == "日柱":
            continue
        tg = get_ten_god(day_stem_idx, p["stem_idx"])
        counts[tg] = counts.get(tg, 0) + 1
    return counts


def count_elements(pillars, day_stem_idx):
    """Count five element appearances across stems and branches."""
    counts = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for p in pillars:
        counts[STEM_ELEMENT[p["stem_idx"]]] += 1
        counts[BRANCH_ELEMENT[p["branch_idx"]]] += 1
    return counts


def assess_day_master_strength(day_stem_idx, month_branch_idx):
    """Assess whether the day master is strong or weak based on birth month."""
    dm_elem = STEM_ELEMENT[day_stem_idx]
    season = MONTH_SEASON.get(month_branch_idx, "平")
    prosperous_elem = SEASON_PROSPEROUS.get(season, "")

    branch = month_branch_idx
    is_earth_month = branch in [1, 4, 7, 10]

    if dm_elem == prosperous_elem:
        return "偏旺"
    elif dm_elem == "土" and is_earth_month:
        return "偏旺"
    elif dm_elem == "土" and prosperous_elem == "火":
        return "偏旺"
    elif dm_elem == "木" and prosperous_elem == "水":
        return "中和"
    elif dm_elem == "火" and prosperous_elem == "木":
        return "中和"
    else:
        return "偏弱"


def generate_suggestions(result):
    """Generate behavioral suggestions based on BaZi chart patterns."""
    pillars = result["pillars"]
    dm = result["day_master"]
    dm_si = HEAVENLY_STEMS.index(dm["stem"])
    dm_elem = dm["element"]

    m_bi = pillars[1]["branch_idx"]
    strength = assess_day_master_strength(dm_si, m_bi)

    tg_counts = count_ten_gods(pillars, dm_si)
    elem_counts = count_elements(pillars, dm_si)

    personality = _suggest_personality(dm_elem, strength, tg_counts, pillars)
    career = _suggest_career(dm_elem, strength, tg_counts, elem_counts)
    relationships = _suggest_relationships(tg_counts)
    health = _suggest_health(elem_counts, dm_elem)

    current_luck = ""
    luck = result["luck"]
    if luck:
        current_luck = _suggest_current_luck(luck, dm_si, strength)

    return {
        "personality": personality,
        "career": career,
        "relationships": relationships,
        "health": health,
        "current_luck": current_luck,
        "strength": strength,
    }


def _suggest_personality(dm_elem, strength, tg_counts, pillars):
    """Generate personality description."""
    traits = []

    elem_traits = {
        "木": "正直向上，有理想抱负，如树木般不断成长",
        "火": "热情主动，充满活力，善于感染周围的人",
        "土": "诚信稳重，踏实可靠，是朋友眼中的定心丸",
        "金": "果断刚毅，讲义气重原则，做事干净利落",
        "水": "聪明灵活，适应力强，思维敏捷善于变通",
    }
    traits.append(elem_traits.get(dm_elem, ""))

    if strength == "偏旺":
        traits.append("自信心强，气场大，有主见不轻易动摇")
    elif strength == "偏弱":
        traits.append("心思细腻，善于合作，懂得借助外力成就自己")
    else:
        traits.append("性格平衡，刚柔并济，能屈能伸")

    if tg_counts.get("正官", 0) >= 2:
        traits.append("责任感强，重视规则和秩序")
    if tg_counts.get("七杀", 0) >= 2:
        traits.append("有魄力和冲劲，敢于挑战权威")
    if tg_counts.get("食神", 0) >= 2 or tg_counts.get("伤官", 0) >= 2:
        traits.append("创造力丰富，喜欢表达自我")
    if tg_counts.get("正财", 0) >= 2 or tg_counts.get("偏财", 0) >= 2:
        traits.append("务实重利，有商业头脑")
    if tg_counts.get("正印", 0) >= 2 or tg_counts.get("偏印", 0) >= 2:
        traits.append("善学习思考，富有智慧和慈悲心")

    return "。".join(traits) + "。" if traits else "性格多元，兼容并蓄。"


def _suggest_career(dm_elem, strength, tg_counts, elem_counts):
    """Generate career suggestions."""
    suggestions = []

    if strength == "偏弱":
        suggestions.append("适合团队协作型工作，或选择稳定的大平台，借助组织力量发展")
        suggestions.append("宜选择能提供持续学习成长环境的行业")

    if strength == "偏旺":
        suggestions.append("适合独立主导型工作，创业或在组织中担任领导角色")
        suggestions.append("宜选择需要强大执行力和决断力的领域")

    elem_careers = {
        "木": "适合教育、文化、环保、医疗等成长型行业",
        "火": "适合传媒、娱乐、互联网、能源等曝光度高的行业",
        "土": "适合房地产、建筑、金融、管理咨询等稳定型行业",
        "金": "适合法律、工程、技术研发、精密制造等专业性强的行业",
        "水": "适合贸易、物流、旅游、咨询、创意设计等流动性强的行业",
    }
    suggestions.append(elem_careers.get(dm_elem, ""))

    if tg_counts.get("食神", 0) + tg_counts.get("伤官", 0) >= 2:
        suggestions.append("有技术/艺术天赋，适合专业技能或创意类工作")
    if tg_counts.get("正官", 0) >= 2:
        suggestions.append("适合公务员、管理岗位或制度完善的大企业")
    if tg_counts.get("正财", 0) + tg_counts.get("偏财", 0) >= 2:
        suggestions.append("有经商天赋，可考虑理财投资或自主创业")

    return "；".join(suggestions) + "。"


def _suggest_relationships(tg_counts):
    """Generate relationship advice."""
    advice = []

    if tg_counts.get("正官", 0) >= 1:
        advice.append("对伴侣忠诚负责，重视家庭稳定")
    if tg_counts.get("七杀", 0) >= 1:
        advice.append("感情中主导欲较强，需学习倾听和妥协")
    if tg_counts.get("伤官", 0) >= 1:
        advice.append("表达直接，需注意沟通方式避免伤害亲近之人")
    if tg_counts.get("正财", 0) >= 1:
        advice.append("对感情务实认真，重视物质基础，是可靠的伴侣")
    if tg_counts.get("劫财", 0) >= 1:
        advice.append("朋友缘好但需注意界限，避免因义气影响亲密关系")
    if tg_counts.get("正印", 0) >= 1:
        advice.append("有包容心和同理心，在关系中乐于付出")

    if not advice:
        advice.append("待人真诚，人际关系和谐")

    return "；".join(advice) + "。"


def _suggest_health(elem_counts, dm_elem):
    """Generate health notes based on element balance."""
    notes = []
    total = sum(elem_counts.values())

    for elem, count in elem_counts.items():
        ratio = count / max(total, 1)
        if ratio < 0.1:
            if elem == "木":
                notes.append("五行木偏弱，注意肝胆保养，避免熬夜，适量舒展运动")
            elif elem == "火":
                notes.append("五行火偏弱，注意心血管健康，保持适度有氧运动")
            elif elem == "土":
                notes.append("五行土偏弱，注意脾胃消化，饮食规律少食生冷")
            elif elem == "金":
                notes.append("五行金偏弱，注意呼吸道保养，空气质量差时做好防护")
            elif elem == "水":
                notes.append("五行水偏弱，注意肾脏泌尿系统，多喝水不久坐")

    for elem, count in elem_counts.items():
        ratio = count / max(total, 1)
        if ratio > 0.35:
            if elem == "木":
                notes.append("木过旺，注意情绪管理，避免过度操劳引起肝火")
            elif elem == "火":
                notes.append("火过旺，注意降火养心，避免亢奋过度引起失眠")
            elif elem == "土":
                notes.append("土过旺，注意饮食清淡，避免脾胃负担过重")
            elif elem == "金":
                notes.append("金过旺，注意肺部健康，避免长期在干燥环境中")
            elif elem == "水":
                notes.append("水过旺，注意肾脏养护，避免寒凉食物")

    if not notes:
        notes.append("五行较为平衡，保持现有生活习惯即可")

    return "；".join(notes) + "。"


def _suggest_current_luck(luck, dm_stem_idx, strength):
    """Generate advice for the current luck period."""
    pillars = luck["pillars"]
    lines = []

    for i, lp in enumerate(pillars[:4]):
        lp_stem_idx = HEAVENLY_STEMS.index(lp["stem"])
        tg = get_ten_god(dm_stem_idx, lp_stem_idx)
        nayin_desc = NAYIN_DESCRIPTIONS.get(lp["nayin"], "")

        dm_elem = STEM_ELEMENT[dm_stem_idx]
        lp_elem = STEM_ELEMENT[lp_stem_idx]
        is_supporting = (
            dm_elem == lp_elem or
            ELEMENT_GENERATED_BY.get(dm_elem) == lp_elem
        )

        if is_supporting and strength == "偏弱":
            assessment = "有利运，宜积极进取"
        elif not is_supporting and strength == "偏旺":
            assessment = "有利运，能量得以释放发挥"
        elif is_supporting and strength == "偏旺":
            assessment = "平稳运，注意避免过于强势"
        else:
            assessment = "调整期，宜韬光养晦积累实力"

        lines.append(
            f"- **{lp['stem']}{lp['branch']}运**（{lp['age_start']:.0f}–{lp['age_end']:.0f}岁）"
            f"：{tg}运，{nayin_desc}。{assessment}"
        )

    return "\n".join(lines)


# =============================================================================
# Luck Cycle (大运)
# =============================================================================

def get_next_jie(year, month, day):
    """Get the next 节 after the birth date."""
    target = date(year, month, day)

    for months_ahead in range(2):
        check_year = year + months_ahead
        check_terms = get_solar_terms_for_year(check_year)
        for jie_idx in JIE_INDICES:
            m, d = check_terms[jie_idx]
            boundary = date(check_year, m, d)
            if boundary > target:
                return boundary

    return None


def get_prev_jie(year, month, day):
    """Get the previous 节 before the birth date."""
    target = date(year, month, day)

    for months_back in range(2):
        check_year = year - months_back
        check_terms = get_solar_terms_for_year(check_year)
        candidates = []
        for jie_idx in JIE_INDICES:
            m, d = check_terms[jie_idx]
            boundary = date(check_year, m, d)
            if boundary < target:
                candidates.append(boundary)
        if candidates:
            return max(candidates)

    return None


def calc_luck_cycle(year, month, day, hour, minute, gender, year_stem_idx,
                    month_stem_idx, month_branch_idx):
    """Calculate luck cycle (大运)."""
    year_stem_is_yang = (year_stem_idx % 2 == 0)

    if gender == "male":
        forward = year_stem_is_yang
    else:
        forward = not year_stem_is_yang

    if forward:
        next_jie = get_next_jie(year, month, day)
        if next_jie:
            days_to_jie = (next_jie - date(year, month, day)).days
        else:
            days_to_jie = 0
    else:
        prev_jie = get_prev_jie(year, month, day)
        if prev_jie:
            days_to_jie = (date(year, month, day) - prev_jie).days
        else:
            days_to_jie = 0

    starting_age = days_to_jie / 3.0

    luck_pillars = []
    for i in range(8):
        if forward:
            ms = (month_stem_idx + i + 1) % 10
            mb = (month_branch_idx + i + 1) % 12
        else:
            ms = (month_stem_idx - i - 1) % 10
            mb = (month_branch_idx - i - 1) % 12

        age_start = starting_age + i * 10
        age_end = age_start + 10

        luck_pillars.append({
            "stem": HEAVENLY_STEMS[ms],
            "branch": EARTHLY_BRANCHES[mb],
            "nayin": get_nayin(ms, mb),
            "age_start": round(age_start, 1),
            "age_end": round(age_end, 1),
        })

    return {
        "direction": "顺排" if forward else "逆排",
        "days_to_jie": days_to_jie,
        "starting_age": round(starting_age, 1),
        "pillars": luck_pillars,
    }


# =============================================================================
# Main Calculation
# =============================================================================

def calculate_bazi(year, month, day, hour=0, minute=0, gender=None):
    """Calculate complete BaZi chart."""
    if year < 1900 or year > 2100:
        raise ValueError(f"Year {year} out of supported range (1900-2100)")

    y_stem, y_branch, y_si, y_bi = calc_year_pillar_for_date(year, month, day)
    m_stem, m_branch, m_si, m_bi = calc_month_pillar(year, month, day)
    d_stem, d_branch, d_si, d_bi = calc_day_pillar(year, month, day)
    h_stem, h_branch, h_si, h_bi = calc_hour_pillar(d_si, hour, minute)

    pillars = [
        {
            "name": "年柱",
            "stem": y_stem,
            "branch": y_branch,
            "stem_idx": y_si,
            "branch_idx": y_bi,
            "nayin": get_nayin(y_si, y_bi),
            "hidden_stems": get_hidden_stems(y_bi),
        },
        {
            "name": "月柱",
            "stem": m_stem,
            "branch": m_branch,
            "stem_idx": m_si,
            "branch_idx": m_bi,
            "nayin": get_nayin(m_si, m_bi),
            "hidden_stems": get_hidden_stems(m_bi),
        },
        {
            "name": "日柱",
            "stem": d_stem,
            "branch": d_branch,
            "stem_idx": d_si,
            "branch_idx": d_bi,
            "nayin": get_nayin(d_si, d_bi),
            "hidden_stems": get_hidden_stems(d_bi),
        },
        {
            "name": "时柱",
            "stem": h_stem,
            "branch": h_branch,
            "stem_idx": h_si,
            "branch_idx": h_bi,
            "nayin": get_nayin(h_si, h_bi),
            "hidden_stems": get_hidden_stems(h_bi),
        },
    ]

    for p in pillars:
        if p["name"] == "日柱":
            p["ten_god"] = "日主"
        else:
            p["ten_god"] = get_ten_god(d_si, p["stem_idx"])

    for p in pillars:
        p["hidden_ten_gods"] = []
        for hs, strength in p["hidden_stems"]:
            hs_idx = HEAVENLY_STEMS.index(hs)
            tg = get_ten_god(d_si, hs_idx)
            p["hidden_ten_gods"].append((hs, strength, tg))

    luck = None
    if gender:
        luck = calc_luck_cycle(year, month, day, hour, minute, gender,
                               y_si, m_si, m_bi)

    return {
        "birth": {
            "year": year,
            "month": month,
            "day": day,
            "hour": hour,
            "minute": minute,
            "gender": gender,
        },
        "day_master": {
            "stem": d_stem,
            "element": STEM_ELEMENT[d_si],
            "yinyang": "阳" if d_si % 2 == 0 else "阴",
        },
        "pillars": pillars,
        "luck": luck,
    }


# =============================================================================
# Markdown Output
# =============================================================================

def format_bazi_markdown(result):
    """Format BaZi result as Markdown."""
    lines = []
    birth = result["birth"]
    dm = result["day_master"]
    pillars = result["pillars"]

    stems = [p["stem"] for p in pillars]
    branches = [p["branch"] for p in pillars]
    nayins = [p["nayin"] for p in pillars]
    tengods = [p["ten_god"] for p in pillars]

    lines.append("# 八字排盘")
    lines.append("")
    lines.append(f"**出生时间**：{birth['year']}年{birth['month']}月{birth['day']}日 "
                 f"{birth['hour']:02d}:{birth['minute']:02d}")
    if birth["gender"]:
        gender_label = "男" if birth["gender"] == "male" else "女"
        lines.append(f"**性别**：{gender_label}")
    lines.append("")

    # Prominent 八字 display
    lines.append("## 八字一览")
    lines.append("")
    lines.append("```")
    lines.append(f"  {'  '.join(stems)}")
    lines.append(f"  {'  '.join(branches)}")
    lines.append("```")
    lines.append("")
    lines.append(
        f"**{pillars[0]['stem']}{pillars[0]['branch']} "
        f"{pillars[1]['stem']}{pillars[1]['branch']} "
        f"{pillars[2]['stem']}{pillars[2]['branch']} "
        f"{pillars[3]['stem']}{pillars[3]['branch']}**"
    )
    lines.append("")
    lines.append(f"**日主**：{dm['stem']}（{dm['element']}・{dm['yinyang']}）")

    suggestions = generate_suggestions(result)
    lines.append(f"**日主强弱**：{suggestions['strength']}")
    lines.append("")

    # Four Pillars table
    lines.append("## 四柱")
    lines.append("")
    pnames = [p["name"] for p in pillars]

    lines.append("|     | " + " | ".join(pnames) + " |")
    lines.append("|-----|" + "|".join(["-----"] * 4) + "|")
    lines.append("| **天干** | " + " | ".join(stems) + " |")
    lines.append("| **地支** | " + " | ".join(branches) + " |")
    lines.append("| **纳音** | " + " | ".join(nayins) + " |")
    lines.append("| **十神** | " + " | ".join(tengods) + " |")
    lines.append("")

    # Hidden Stems
    lines.append("## 藏干")
    lines.append("")
    for p in pillars:
        hs_str = "、".join([f"{s}（{t}）" for s, t in p["hidden_stems"]])
        htg_str = "、".join([f"{s}→{tg}" for s, _, tg in p["hidden_ten_gods"]])
        lines.append(f"- **{p['name']}** {p['branch']}：{hs_str} ／ 十神：{htg_str}")
    lines.append("")

    # Na Yin Analysis
    lines.append("## 纳音解析")
    lines.append("")
    for p in pillars:
        desc = NAYIN_DESCRIPTIONS.get(p["nayin"], "")
        lines.append(f"- **{p['name']}** {p['stem']}{p['branch']} → **{p['nayin']}**：{desc}")
    lines.append("")

    # Luck Cycle
    luck = result["luck"]
    if luck:
        lines.append("## 大运")
        lines.append("")
        lines.append(f"- **排法**：{luck['direction']}")
        lines.append(f"- **起运天数**：{luck['days_to_jie']} 天")
        lines.append(f"- **起运年龄**：{luck['starting_age']} 岁")
        lines.append("")
        lines.append("| 大运 | 天干 | 地支 | 纳音   | 年龄         |")
        lines.append("|------|------|------|--------|--------------|")
        for i, lp in enumerate(luck["pillars"]):
            age_range = f"{lp['age_start']:.0f}–{lp['age_end']:.0f}岁"
            lines.append(
                f"| {i+1} | **{lp['stem']}** | **{lp['branch']}** | {lp['nayin']} | {age_range} |"
            )
        lines.append("")

    # Behavioral Suggestions
    lines.append("## 行为建议")
    lines.append("")

    lines.append("### 性格特点")
    lines.append(suggestions["personality"])
    lines.append("")

    lines.append("### 事业方向")
    lines.append(suggestions["career"])
    lines.append("")

    lines.append("### 人际关系")
    lines.append(suggestions["relationships"])
    lines.append("")

    lines.append("### 健康注意")
    lines.append(suggestions["health"])
    lines.append("")

    if suggestions["current_luck"]:
        lines.append("### 大运提示")
        lines.append(suggestions["current_luck"])
        lines.append("")

    lines.append("---")
    lines.append("*注：节气日期为近似计算，极端情况可能偏差1日。以上分析仅供参考，不可作为重大决策的唯一依据。*")

    return "\n".join(lines)


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="BaZi (八字) Calculator — Four Pillars of Destiny",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python bazi.py 1990 5 15 8 30
  python bazi.py 1990 5 15 8 30 --gender male
  python bazi.py 1990 5 15 8 30 --gender female --json
        """,
    )
    parser.add_argument("year", type=int, help="Birth year (1900-2100)")
    parser.add_argument("month", type=int, help="Birth month (1-12)")
    parser.add_argument("day", type=int, help="Birth day (1-31)")
    parser.add_argument("hour", type=int, nargs="?", default=0,
                        help="Birth hour 0-23 (default: 0)")
    parser.add_argument("minute", type=int, nargs="?", default=0,
                        help="Birth minute 0-59 (default: 0)")
    parser.add_argument("--gender", "-g", choices=["male", "female"],
                        help="Gender for luck cycle calculation")
    parser.add_argument("--json", "-j", action="store_true",
                        help="Output as JSON instead of Markdown")

    args = parser.parse_args()

    try:
        result = calculate_bazi(args.year, args.month, args.day,
                                args.hour, args.minute, args.gender)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    else:
        print(format_bazi_markdown(result))


if __name__ == "__main__":
    main()
