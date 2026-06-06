---
name: bazi-calculator
description: Calculate BaZi (八字/Four Pillars of Destiny) from a birth date and time. Use whenever the user mentions 八字, 算八字, 排盘, 四柱, BaZi, Four Pillars, 生辰八字, 日柱, 大运, 十神, 纳音, luck cycle, or wants to know their Chinese zodiac destiny chart. Even if the user just provides a birth date and asks "what does this mean" in a Chinese metaphysical context, use this skill.
---

# BaZi Calculator (八字排盘)

Calculate a complete BaZi (Four Pillars of Destiny) chart from a Gregorian birth date and time.

## Usage

### Step 1: Collect birth information

Ask the user for:
- **出生日期**：公历年、月、日（如 1990年5月15日）
- **出生时间**：小时和分钟（如 上午8:30）
- **性别**：男/女（计算大运必须）

If the user provides incomplete info, ask only for what's missing. Do not re-ask for info already given.

### Step 2: Run the calculation

Execute the script with the collected info:

```bash
python3 <skill-path>/scripts/bazi.py <year> <month> <day> <hour> <minute> --gender <male/female>
```

- `<skill-path>` is the absolute path to this skill directory
- Hour is 0-23 (convert "上午8点" to 8, "下午3点" to 15)
- If minute is unknown, use 0
- If gender is unknown (大运无法计算), omit `--gender` — luck cycle will be skipped

For JSON output (when needing to process further), add `--json`.

### Step 3: Present the result

Show the Markdown output from the script directly to the user. The output includes:

1. **四柱 (Four Pillars)** — year, month, day, hour pillars with stems, branches, Na Yin, and Ten Gods
2. **藏干 (Hidden Stems)** — hidden stems in each earthly branch with their Ten God relationships
3. **大运 (Luck Cycle)** — 8 luck periods of 10 years each, with starting age

After presenting the chart, offer a brief plain-language summary:
- What the day master (日主) element and its strength suggest about the person's basic nature
- Any notable patterns (e.g., many of the same Ten God appearing)

Do NOT make extreme predictions or claims. Keep the tone informative and measured.

## Important notes

- The calculation uses approximate solar term dates (may vary by ±1 day at boundaries)
- Year range: 1900-2100
- 年柱以立春为界，月柱以节气为界
- Results are for reference only — remind users of this when asked about life decisions

## How it works

The script `scripts/bazi.py` performs these calculations:
- **Year Pillar**: Based on the 立春 (Start of Spring) boundary
- **Month Pillar**: Based on 12 solar terms, stem derived via 五虎遁
- **Day Pillar**: Continuous 60-day sexagenary cycle from reference date 1900-01-01
- **Hour Pillar**: Based on 2-hour periods (时辰), stem derived via 五鼠遁
- **Hidden Stems**: Standard 藏干 table for each earthly branch
- **Ten Gods**: Relationship between day stem and all other stems
- **Na Yin**: 纳音五行 from the 60-position sexagenary cycle
- **Luck Cycle**: Direction based on year stem yin/yang × gender, starting age from days to nearest 节

Reference data is in `references/tables.md` for lookups during interpretation.
