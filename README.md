# Daily Hanzi Dictionary Database (每日汉字词库)

本项目基于开源汉英词典数据集 [hanyingcidian](https://github.com/1418731519shuer/hanyingcidian) 整理，去除了原仓库的自述文件，并针对软件开发（如 Flutter、Android、iOS 或后端服务）的高性能查询需求，将 215MB 的 CSV 词典数据转换并写成了优化且带索引的 **SQLite 软件词库**。

## 目录结构
- `clean_dict.csv.zip` : 原始 CSV 数据集的 ZIP 压缩包 (约 57MB)。解压后可获得 215MB 的 `clean_dict.csv`。
- `daily_hanzi.db.zip` : 已建立索引的 SQLite 数据库的 ZIP 压缩包 (约 72MB)。解压后可获得 245MB 的 `daily_hanzi.db` 软件词库。
- `convert_to_db.py` : 用于将 CSV 文件转换为 SQLite 数据库的 Python 转换脚本。
- `verify_db.py` : 用于测试数据库完整性与查询性能的 Python 验证脚本。

> [!NOTE]
> 由于 GitHub 单个文件 100MB 的限制以及 Git LFS 服务器的不稳定性，我们将大型数据文件压缩为 ZIP 包提交。在使用或运行测试前，请先将 `.zip` 文件解压到当前目录下。

---

## 软件词库 (SQLite) 结构说明

数据库文件为 `daily_hanzi.db`，包含单张主表 `dictionary`。

### 数据表：`dictionary`

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `word_id` | INTEGER PRIMARY KEY | 唯一主键 ID |
| `simplified` | TEXT NOT NULL | 简体字词头 (如: `学习`, `木`) |
| `pinyin` | TEXT NOT NULL | 机读拼音，带数字声调 (如: `xue2 xi2`) |
| `pinyin_display` | TEXT NOT NULL | 拼音显示，带声调符号 (如: `xuéxí`) |
| `brief` | TEXT | 简短英文释义 |
| `origin` | TEXT | 词源说明 |
| `meaning` | TEXT | 详细英文释义 |
| `usage` | TEXT | 用法说明 |
| `tags` | TEXT | 主题标签 (JSON格式) |
| `hsk_level` | TEXT | HSK 等级 (新/旧等级，无则为空) |
| `status` | TEXT | 词条状态 (如 `cedict` 等) |
| `part_of_speech` | TEXT | 词性 |
| `measure_word` | TEXT | 量词 (JSON数组形式) |
| `grammar_pattern` | TEXT | 语法结构 (JSON数组形式) |
| `frequency_rank` | INTEGER | 词频排名 |
| `simple_example` | TEXT | 中英双语例句 (JSON格式) |
| `valency` | TEXT | 配价说明 |
| `synonyms` | TEXT | 同义词 (JSON数组) |
| `antonyms` | TEXT | 反义词 (JSON数组) |
| `near_synonyms` | TEXT | 近义词 (JSON数组) |
| `near_synonym_distinction` | TEXT | 近义词辨析 |
| `collocations` | TEXT | 常见搭配 (JSON数组) |
| `register` | TEXT | 语域 (如 formal, colloquial) |
| `cedict_definitions` | TEXT | CC-CEDICT 原始释义 (JSON数组) |
| `src_xiandai_da` | INTEGER | 来源标识：现代汉语大词典 (1或0) |
| `src_zhonghua` | INTEGER | 来源标识：中華語文大辭典 (1或0) |
| `src_guifan` | INTEGER | 来源标识：现代汉语规范词典 (1或0) |
| `src_xiandai7_py` | INTEGER | 来源标识：现代汉语词典第7版拼音 (1或0) |
| `src_xiandai7` | INTEGER | 来源标识：现代汉语词典第7版 (1或0) |
| `src_jindai` | INTEGER | 来源标识：近代汉语词典 (1或0) |
| `src_gudai` | INTEGER | 来源标识：古代汉语词典第1版 (1或0) |
| `src_taiwan` | INTEGER | 来源标识：臺灣台語常用詞辭典 (1或0) |
| `src_liangan` | INTEGER | 来源标识：两岸差异用词 (1或0) |

### 数据库索引 (Indexes)
为了在客户端软件中实现毫秒级的汉字与拼音实时联想、模糊匹配和精确检索，数据库中预建了以下 B-Tree 索引：
1. `idx_dict_simplified` : 针对 `simplified` 字段的索引（用于按汉字查找，查询耗时仅约 0.03ms）。
2. `idx_dict_pinyin` : 针对 `pinyin` 字段的索引（用于数字声调拼音检索）。
3. `idx_dict_pinyin_display` : 针对 `pinyin_display` 字段的索引（用于带符号拼音检索）。
4. `idx_dict_hsk` : 针对 `hsk_level` 字段的索引（用于按 HSK 级别筛选单词）。

---

## 快速使用指南 (Python 示例)

你可以使用以下 Python 代码快速查询词库：

```python
import sqlite3

# 连接数据库
conn = sqlite3.connect('daily_hanzi.db')
cursor = conn.cursor()

# 精确查询“学习”的拼音与释义
cursor.execute("SELECT pinyin_display, brief, simple_example FROM dictionary WHERE simplified = ? LIMIT 1", ("学习",))
result = cursor.fetchone()

if result:
    pinyin, brief, example = result
    print(f"拼音: {pinyin}")
    print(f"释义: {brief}")
    print(f"例句: {example}")

conn.close()
```

## 重新构建词库
如果修改了 `clean_dict.csv`，可以运行以下命令重新生成数据库：
```bash
python convert_to_db.py
```
