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
        # For years outside range, use 21st century values with adjustment
        return c_21st[term_index]


def get_solar_term_date(year, term_index):
    """Get the approximate date of a solar term.

    Args:
        year: Gregorian year
        term_index: 0=小寒, 1=大寒, ..., 23=冬至

    Returns:
        (month, day) tuple (approximate, may be off by 1 day)
    """
    if term_index >= 12:
        # Second half of solar terms may use the previous year's offset
        y = year - 1900
    else:
        y = year - 1900

    c = _solar_term_c(year, term_index)
    day = int(c + 0.2422 * y - int(y / 4))

    # Map term index to month
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
    """Determine which month branch (0-11, starting with 寅=0) a date falls in.

    Uses solar terms to determine month boundaries.
    Returns month index (0=寅月, ..., 11=丑月).
    """
    terms = get_solar_terms_for_year(year)

    target = date(year, month, day)

    month_boundaries = []

    for i, jie_idx in enumerate(JIE_INDICES):
        if jie_idx == 0:  # 小寒 — in January, but belongs to the next year's Jan
            m, d = terms[jie_idx]
            boundary_date = date(year, m, d)
        else:
            m, d = terms[jie_idx]
            boundary_date = date(year, m, d)
        month_boundaries.append((i, boundary_date))

    # Now determine which month the target date falls in
    # Sort boundaries by date
    sorted_boundaries = sorted(month_boundaries, key=lambda x: x[1])

    # Find the last boundary <= target
    month_idx = None
    for mi, bd in reversed(sorted_boundaries):
        if target >= bd:
            month_idx = mi
            break

    if month_idx is None:
        # Before first boundary of the year (before 立春)
        # It's still in month 11 (丑月) of previous year
        month_idx = 11

    return month_idx


# =============================================================================
# Pillar Calculations
# =============================================================================

def calc_year_pillar(year):
    """Calculate year pillar (年柱).

    The year pillar changes at 立春, not January 1.
    We check if the date is before 立春 of this year.
    """
    # Year stem: (year - 4) % 10
    # Year branch: (year - 4) % 12
    stem = HEAVENLY_STEMS[(year - 4) % 10]
    branch = EARTHLY_BRANCHES[(year - 4) % 12]
    return stem, branch, (year - 4) % 10, (year - 4) % 12


def calc_year_pillar_for_date(year, month, day):
    """Calculate year pillar considering 立春 boundary."""
    # Get 立春 date for this year
    lichun_m, lichun_d = get_solar_term_date(year, 2)
    target = date(year, month, day)
    lichun = date(year, lichun_m, lichun_d)

    if target < lichun:
        # Date is before 立春, use previous year's pillar
        year -= 1

    return calc_year_pillar(year)


def calc_month_pillar(year, month, day):
    """Calculate month pillar (月柱).

    The month branch is determined by which solar term range the date falls in.
    Month stem is determined by year stem (五虎遁): (year_stem_idx * 2 + month_idx) % 10
    """
    month_idx = get_month_index_for_date(year, month, day)
    _, _, year_stem_idx, _ = calc_year_pillar_for_date(year, month, day)

    month_stem_idx = (year_stem_idx * 2 + month_idx) % 10
    month_branch_idx = (month_idx + 2) % 12  # 寅=2, 卯=3, ..., 丑=1

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
    """Calculate day pillar (日柱).

    Reference: 1900-01-01 = 甲戌日 (stem=0, branch=10)
    """
    delta = day_number_from_1900(year, month, day)
    stem_idx = delta % 10
    branch_idx = (delta + 10) % 12
    return HEAVENLY_STEMS[stem_idx], EARTHLY_BRANCHES[branch_idx], stem_idx, branch_idx


def calc_hour_pillar(day_stem_idx, hour, minute):
    """Calculate hour pillar (时柱).

    Hour branch is determined by the two-hour period.
    Hour stem is determined by day stem (五鼠遁): (day_stem_idx * 2 + hour_branch_idx) % 10
    """
    total_minutes = hour * 60 + minute

    if total_minutes >= 23 * 60 or total_minutes < 1 * 60:
        hour_branch_idx = 0  # 子
    elif total_minutes < 3 * 60:
        hour_branch_idx = 1  # 丑
    elif total_minutes < 5 * 60:
        hour_branch_idx = 2  # 寅
    elif total_minutes < 7 * 60:
        hour_branch_idx = 3  # 卯
    elif total_minutes < 9 * 60:
        hour_branch_idx = 4  # 辰
    elif total_minutes < 11 * 60:
        hour_branch_idx = 5  # 巳
    elif total_minutes < 13 * 60:
        hour_branch_idx = 6  # 午
    elif total_minutes < 15 * 60:
        hour_branch_idx = 7  # 未
    elif total_minutes < 17 * 60:
        hour_branch_idx = 8  # 申
    elif total_minutes < 19 * 60:
        hour_branch_idx = 9  # 酉
    elif total_minutes < 21 * 60:
        hour_branch_idx = 10  # 戌
    else:
        hour_branch_idx = 11  # 亥

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
    """Calculate the position (0-59) in the sexagenary cycle.

    The cycle pairs stems and branches advancing together.
    Position n has stem n%10 and branch n%12.
    We solve: n ≡ stem_idx (mod 10), n ≡ branch_idx (mod 12)
    """
    # Precomputed lookup for all 60 pairs
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

# Element generation/control relationships
ELEMENT_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
ELEMENT_GENERATED_BY = {"火": "木", "土": "火", "金": "土", "水": "金", "木": "水"}
ELEMENT_CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
ELEMENT_CONTROLLED_BY = {"土": "木", "水": "土", "火": "水", "金": "火", "木": "金"}


def get_ten_god(day_stem_idx, target_stem_idx):
    """Calculate ten god (十神) relationship.

    Args:
        day_stem_idx: Day stem index (日主)
        target_stem_idx: Target stem index

    Returns:
        Ten god name in Chinese
    """
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
        # Day stem generates target (我生)
        return "食神" if same_yy else "伤官"
    elif ELEMENT_GENERATED_BY[day_elem] == target_elem:
        # Target generates day stem (生我)
        return "偏印" if same_yy else "正印"
    elif ELEMENT_CONTROLS[day_elem] == target_elem:
        # Day stem controls target (我克)
        return "偏财" if same_yy else "正财"
    elif ELEMENT_CONTROLLED_BY[day_elem] == target_elem:
        # Target controls day stem (克我)
        return "七杀" if same_yy else "正官"

    return "未知"


# =============================================================================
# Luck Cycle (大运)
# =============================================================================

def get_next_jie(year, month, day):
    """Get the next 节 after the birth date."""
    target = date(year, month, day)

    for months_ahead in range(2):  # current year and next year
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

    for months_back in range(2):  # current year and previous year
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
    """Calculate luck cycle (大运).

    Returns:
        dict with starting_age, luck_pillars list
    """
    year_stem_is_yang = (year_stem_idx % 2 == 0)  # 甲丙戊庚壬 → yang

    if gender == "male":
        forward = year_stem_is_yang  # male + yang year → forward
    else:
        forward = not year_stem_is_yang  # female + yin year → forward

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

    # Starting age: 3 days = 1 year of life
    starting_age = days_to_jie / 3.0

    # Generate 8 luck pillars (each spans 10 years)
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
    """Calculate complete BaZi chart.

    Args:
        year: Gregorian year (1900-2100)
        month: Gregorian month (1-12)
        day: Gregorian day (1-31)
        hour: Hour (0-23)
        minute: Minute (0-59)
        gender: "male" or "female" (optional, for luck cycle)

    Returns:
        dict with all BaZi components
    """
    if year < 1900 or year > 2100:
        raise ValueError(f"Year {year} out of supported range (1900-2100)")

    # Year pillar
    y_stem, y_branch, y_si, y_bi = calc_year_pillar_for_date(year, month, day)

    # Month pillar
    m_stem, m_branch, m_si, m_bi = calc_month_pillar(year, month, day)

    # Day pillar
    d_stem, d_branch, d_si, d_bi = calc_day_pillar(year, month, day)

    # Hour pillar
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

    # Ten Gods for each pillar (relative to day stem)
    for p in pillars:
        if p["name"] == "日柱":
            p["ten_god"] = "日主"
        else:
            p["ten_god"] = get_ten_god(d_si, p["stem_idx"])

    # Ten Gods for hidden stems in each pillar
    for p in pillars:
        p["hidden_ten_gods"] = []
        for hs, strength in p["hidden_stems"]:
            hs_idx = HEAVENLY_STEMS.index(hs)
            tg = get_ten_god(d_si, hs_idx)
            p["hidden_ten_gods"].append((hs, strength, tg))

    # Luck cycle
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

    # Header
    lines.append("# 八字排盘")
    lines.append("")
    lines.append(f"**出生时间**：{birth['year']}年{birth['month']}月{birth['day']}日 "
                 f"{birth['hour']:02d}:{birth['minute']:02d}")
    if birth["gender"]:
        gender_label = "男" if birth["gender"] == "male" else "女"
        lines.append(f"**性别**：{gender_label}")
    lines.append(f"**日主**：{dm['stem']}（{dm['element']}・{dm['yinyang']}）")
    lines.append("")

    # Four Pillars table
    lines.append("## 四柱")
    lines.append("")
    pillars = result["pillars"]
    pnames = [p["name"] for p in pillars]
    stems = [p["stem"] for p in pillars]
    branches = [p["branch"] for p in pillars]
    nayins = [p["nayin"] for p in pillars]
    tengods = [p["ten_god"] for p in pillars]

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

    lines.append("---")
    lines.append("*注：节气日期为近似计算，极端情况可能偏差1日。八字排盘结果仅供参考。*")

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
