# JOHD Data Paper — 骨架（依官方模板）
字數上限 1,000–1,500（不含 title/affiliation/abstract/圖表/references；含圖表說明與註腳）
⚠️ 內文與摘要**不得**取自資料庫既有說明文字，必須改寫。

---

## Title
Colonial Taiwan Social-Administration Statistics, 1895–1945:
Education, Health Services, and Poor Relief

## Authors / Affiliations
【TODO】姓名、系所、通訊作者 email

## Author roles
【TODO】依 CRediT taxonomy（credit.niso.org）逐位標示

## Abstract（約 100 字）
【TODO 改寫，不可抄襲來源網站】需涵蓋：資料涵蓋什麼、如何蒐集、如何存放、重用潛力。
可用素材：50 張表、1897–1945、三個社會行政領域、來源為 1946 年官方統計彙編、
以 tidy 長格式重製並附逐格出處。

## Keywords（最多 6，除專名外小寫）
colonial taiwan; historical statistics; education; public health; poor relief; data rescue

---

# (1) Overview

## Repository location
【TODO】Zenodo DOI —— **必須在投稿前完成存放並取得 DOI，否則直接退稿**

## Context
本資料集為【大學名稱】數位史學課程之課程作業（coursework）成果。
※ JOHD 模板明文將 course work 列為正當來源，照實寫即可。
【TODO】若日後用於其他論文，於此列出書目資訊

---

# (2) Method ← **全篇重心，約 500–600 字**

## Steps
- **來源**：《臺灣省五十一年來統計提要》（1894–1945），
  1946 年臺灣省行政長官公署統計室編；中研院資訊所數位化為 .xls
  （http://twstudy.iis.sinica.edu.tw/twstatistic50/）
- **選錄範圍**：24 章中的 3 章 —— 教育（17 表）、衛生醫療保健（16 表）、
  各宗教及救助（17 表），共 **50 表**。選錄理由見 §4
- **取得**：2026-09-09 全數下載成功（50/50，1.6 MB），全部可程式化解析
- **處理**：Python；`normalize.py`（紀年與缺值）、`reshape.py`（多層表頭→長格式）
  【TODO】程式碼 repo 連結

## Sampling strategy
非抽樣：所選三章之表格**全數納入**。
【TODO】驗證用抽樣方案見 §Quality control

## Quality control
原始檔的系統性問題（已量化）：
| 問題 | 影響 |
|---|---|
| 缺值以「.」表示（非標準 NA） | 48 / 50 檔 |
| `└─N─┘` 跨欄合併偽影 | 10 / 50 檔 |
| 多層中文表頭造成空白儲存格 | 平均 21% |
| 民國／日本紀年混用、字間夾空白 | 全部 |

處理與驗證：
- 紀年正規化：2,440 個標記中自動解出 **2,221（91.0%）**，餘者人工判定
- **期間型態必須分離**：fiscal_year_end 850／calendar_year 814／
  year_end 490／fiscal_year 67 —— 逾半數非曆年，合併將產生無聲錯誤
- 表頭重建自動正確率約 **78%**（字元散置於多欄者需 per-table 覆寫）
- 每筆保留 `src_row`/`src_col`，可回溯原始儲存格
- 【TODO】**人工驗證**：抽樣 N 筆比對原表，報告正確率
- 【TODO】**標註者間一致性**：兩位獨立標註者，報告 Cohen's κ

---

# (3) Dataset Description

| 欄位 | 內容 |
|---|---|
| Repository name | Zenodo |
| Object name | 【TODO】 |
| Format names and versions | CSV (UTF-8)、tidy long format；原始 .xls 另存 raw/ |
| Creation dates | 2026-09-09 – 【TODO】 |
| **Dataset creators** | 【TODO 作者】＋**須列出中研院資訊所（原數位化者）** |
| Language | 中文（繁體）；欄位名英文 |
| License | CC BY 4.0（原書為政府公文書；數值為事實） |
| Publication date | 【TODO】 |

---

# (4) Reuse Potential（約 300–400 字）

## 可重用之處
- 教育、衛生行政、社會救助三領域的長期序列（多數表 40 年以上）
- 既有的日治統計數值化工作集中於**人口、農業、貿易、價格、財政、土地**
  （臺大經濟系吳聰敏／Kelly Olds、一橋大學 ASHSTAT、HMD/HFD、CTHRD），
  **本三領域未被涵蓋** —— 因其非經濟學問題
- 可與現代資料銜接（如疾管署傳染病統計）做長時段比較
- 教學用途：多層表頭、紀年換算、缺值語意皆為實例教材

## 限制與障礙（模板規定必寫）
- **1895–1896 完全無資料**
- **1943 年斷崖**：涵蓋表數自 43 降至 15；28/48 表終止於 1942；僅 3 表達 1945
- **早期年份（1897–1905）表數由 6 增至 32**，數值上升可能反映統計能力擴張而非現象變化
- 【TODO】蕃地／原住民地區涵蓋狀況待查
- 【TODO】1920 年州廳制改制對地理單位可比性的影響待查
- 本資料集為二手彙編（1946 年接收方所編）之再處理，非原始統計書

---

# 後置
- Acknowledgements：【TODO】
- Funding statement：【TODO】
- **Competing interests**：The author(s) has/have no competing interests to declare.
- References：APA 格式，附 DOI
- **AI Declaration**（必填）：【TODO】需聲明生成式 AI 用於資料採集腳本、
  格式轉換與初稿撰寫；**所有人工驗證由作者執行**；作者承擔全部正確性責任
- Supplementary Files：【TODO】

---

# Cover letter 要點
1. 通訊作者單位與聯絡方式
2. 為何適合 JOHD —— 點名先例（如 Modernism's Vector，johd.485，中文語料先例）
3. **APC waiver 申請理由**（APC £1,070，學生身分）
4. （可選）建議三位審查人
