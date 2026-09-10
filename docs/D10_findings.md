# D10 tidy schema 與 reshape 原型（完成 2026-09-09）— schema 驗證通過，並測出關鍵限制

## 已驗證的 tidy schema（9 欄）
| 欄位 | 說明 |
|---|---|
| `table_id` | 原表編號（Mt468） |
| `year` | 西元年 |
| `period_type` | calendar_year / year_end / fiscal_year / fiscal_year_end |
| `dim1` | 第一層分類（學校類別） |
| `dim2` | 第二層分類（校數／教員數／學生數） |
| `value` | 數值 |
| `flag` | missing_dot / bracket_artifact / non_numeric |
| **`src_row` / `src_col`** | **原始儲存格座標 → 每一筆都可回溯原表** |

`src_row`/`src_col` 直接滿足 data paper 的「出處可追溯」要求。

## 實測（Edu_Mt468 歷年全省學校及員生數）
原始 61×31 → **tidy 1,380 列**，有效數值 **1,137**，缺值 243（皆標為 `missing_dot`）
年份 **1899–1944**，全表 period_type = `fiscal_year_end`
dim2 完全正確：校數 460／教員數 460／學生數 460

## ⚠️ 測出的關鍵限制：表頭字元被拆散於多欄
原表為求版面美觀，把「大學」「私立」等標題**逐字散置於不同欄位**
（第4列：`NaN|大|NaN|學|專門學校|…`），而非合併儲存格。

結果：
- ✅ 正確：專門學校・師範學校・中等學校・職業學校・國民學校・盲啞學校・特種學校（各 138 筆）
- ❌ 破碎：`大`(92)、`學`(46)、`私`(92) —— 應為「大學」「私立」

**7/9 類別自動正確，2 類需人工修正 → 約 78% 自動化率。**

### 這證實了先前的工作量估計
**不存在通用演算法，每張表需要人工檢視與 per-table 覆寫。**
`reshape()` 已加入 `dim_overrides` 參數供逐表修正。
50 表 × 人工檢視 ≈ 25–50 小時的估計成立。

### 而且這正是論文的賣點
「表頭字元散置」這類問題無法自動偵測，只能靠人讀。
一個經過人工檢視、每筆可回溯原始儲存格的資料集，
與既有零散 .xls 的差別就在這裡 —— 寫進 Quality Control 節。

## 已交付
- `scripts/reshape.py`（含 `dim_overrides` 機制）
- `docs/sample_tidy_Mt468.csv`（1,380 筆實際輸出，可直接檢視）

## 下一步
- codebook 範本
- 逐表建立 dim_overrides 樣式庫（先做 Edu 17 表）
