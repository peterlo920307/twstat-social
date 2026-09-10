# T02 檢索欄位、內容摘要填充、影像取得（完成 2026-09-09）

## 完整欄位對照表（從 select option value 取得）
| API 欄位名 | 中文 |
|---|---|
| `_all` | 全欄位 |
| `identifier` | 典藏號 |
| `zong` | 全宗系列 |
| `meeting_level` | 會議階層 |
| `category_level` | 分類階層 |
| `collection_name` | 題名 |
| `date_string` | 日期描述 |
| **`abstract_mask`** | **內容摘要** |
| `chairman` | 主席 |
| `main_mamber` | 主要議員（系統原拼字如此） |
| `fileno` | 相關文號 |
| `reference` | 參照資料 |
| `list_member` | 相關人名 |
| `list_organ` | 相關單位 |
| `list_subject` | 相關主題 |
| `list_location` / `location` | 相關地點 / 相關地名 |
| `yearrange` | 年代統計 |
| `termpat` / `clipterm` | 綴詞 / 夾詞查詢 |

## 端點
`Archive/search/`、`Archive/export/page/`、`Archive/export/result/`、`Display/`、`Archive/index`、`Archive/myapply/`

## 實測命中數
- `_all=質詢` → 29,779
- `_all=教育` → 26,027
- `chairman=黃朝琴` → 5,229
- **`abstract_mask=水利` → 1,938**
- `list_member=李萬居` → 315
- `category_level=質詢` → 語法未命中（值格式需再試，可能需階層字串）

## 決定性結論
**`abstract_mask`（內容摘要）可全文檢索且回傳實質命中數 → 摘要欄位是有填充的真實文字，不是空殼。**
→ 這批史料**有機器可讀文字，不必然需要 OCR**。專案難度大幅下降。
**`chairman` 與 `list_member` 可查 → 發言者層級的檢索可行**，配合 369 位議員傳記可建 speaker 權威檔。

## 未解（轉 T03）
- 結果清單為 AJAX 渲染，尚未取得單筆記錄的完整欄位內容（需解 `Archive/search/` 或 `Display/` 的回傳格式）
- `Archive/export/result/`（下載目錄）需正確選取狀態
- 影像檔案格式與取得方式未測（優先度因摘要可用而下降）
- `category_level` 的值格式
