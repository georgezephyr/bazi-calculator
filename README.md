# bazi-calculator

Claude Code skill for calculating **BaZi (八字)** — the Four Pillars of Destiny, a traditional Chinese metaphysical system.

## Features

- **四柱 (Four Pillars)**: Year, Month, Day, Hour stems and branches
- **藏干 (Hidden Stems)**: Hidden heavenly stems in each earthly branch
- **十神 (Ten Gods)**: Relationship between day master and all stems
- **纳音 (Na Yin)**: Na Yin five elements for each pillar
- **大运 (Luck Cycle)**: 8 luck periods of 10 years each

## Installation

### As a Claude Code skill

```bash
# Clone to the skills directory
git clone https://github.com/georgezephyr/bazi-calculator.git ~/.claude/skills/bazi-calculator
```

Then restart Claude Code or start a new conversation. The skill triggers when you mention 八字, 排盘, BaZi, Four Pillars, etc.

### Standalone usage

```bash
python3 scripts/bazi.py 1990 5 15 8 30 --gender male
```

## Requirements

- Python 3.7+ (standard library only, no dependencies)

## Example

```
> 帮我算一下八字，1990年5月15日上午8点半，男

# 八字排盘

**出生时间**：1990年5月15日 08:30
**性别**：男
**日主**：庚（金・阳）

## 四柱

|     | 年柱 | 月柱 | 日柱 | 时柱 |
|-----|-----|-----|-----|-----|
| **天干** | 庚 | 己 | 庚 | 庚 |
| **地支** | 午 | 巳 | 辰 | 辰 |
| **纳音** | 路旁土 | 大林木 | 白蜡金 | 白蜡金 |
| **十神** | 比肩 | 正印 | 日主 | 比肩 |
```

## Important Notes

- Solar term dates are approximate (may vary by ±1 day at boundaries)
- Year range: 1900-2100
- Results are for reference only

## License

MIT
