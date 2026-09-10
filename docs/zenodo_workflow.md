# Zenodo 存放與 DOI 流程

## 必填欄位（Zenodo 官方規格，已查證）
`upload_type`（本案 = `dataset`）、`publication_date`（ISO8601）、`title`、
`creators`（`name` 須為 **"Family, Given"** 格式）、`description`、
`access_right`（本案 = `open`）、`license`（access_right 為 open 時必填）

選填但**本案應填**：`version`（建議語意化版號）、`language`（ISO 639-2/3，中文用 `zho`）、
`keywords`、`dates`、`method`、`related_identifiers`、`notes`

## 已交付
專案根目錄的 **`.zenodo.json`**，欄位已依規格填好，
待填處以 `TODO-` 標記（作者、ORCID、日期、description、method）。

⚠️ **授權需分開標示**：程式碼 MIT（`LICENSE`），資料與文件 CC BY 4.0
（`LICENSE-DATA`）。Zenodo 只能選一種，選 CC BY 4.0 並在 description
說明程式碼部分為 MIT。

## 執行順序（順序不可顛倒）
1. **先完成資料整理與驗證**（tidy CSV + CODEBOOK.md + 驗證報告）
2. 打包上傳 Zenodo：
   - `data/` tidy.csv、notes.csv、validation_sample.csv（皆 UTF-8）
   - **`raw/` 不重新散布**：原始 .xls 為中研院 2006 年數位化成果，
     改附 `scripts/download_raw.py` 供他人自行取得（見 DESIGN.md §10）
   - `docs/` CODEBOOK.md、DESIGN.md、EXAMPLE.md、bias_statement.md、
     W05_generalisation.md、W06_layout.md、CODING_SHEET.md
   - `src/twstat/` 套件本身（原規劃的 normalize.py／reshape.py／
     make_validation_sample.py 已改寫為套件模組）
   - `.zenodo.json`、README、LICENSE（MIT）、LICENSE-DATA（CC BY 4.0）
3. **取得 DOI**
4. **再投稿 JOHD** —— 投稿前無 DOI 會被直接退稿

## 版本策略
- `1.0.0` = 教育 17 表（v0.1 先行版可用 `0.1.0`）
- `1.1.0` = 加入衛生 16 表
- `1.2.0` = 加入社會救助 17 表
- Zenodo 的 Concept DOI 恆定指向最新版，各版另有獨立 DOI

## 授權判斷（已於 T06/D01 查證）
- 原書為 1946 年政府公文書 → **著作權法第 9 條，不得為著作權標的**
- 中研院所做為格式轉換；本資料集內容為**數值＝事實**，不受著作權保護
- 故採 **CC BY 4.0**
- ⚠️ `notes` 欄的法律敘述**投稿前請與系上或圖書館確認一次**

## 必須列名的貢獻者
JOHD 模板明訂 Dataset creators 須列出所有協助建立資料集者（即使非論文作者）：
- **中央研究院資訊科學研究所**（原始數位化）
- 原編纂單位：臺灣省行政長官公署統計室（1946）
