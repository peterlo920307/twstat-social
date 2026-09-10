# D01 日治時期統計檔案資料庫介面拆解（完成 2026-09-09）

## 站台結構（純 PHP + GET/POST，易處理）
- `main_browse.php` — 階層瀏覽，**已抽出 1,325 個 level 代碼**
- `query.php?Action_From=level&lvbw=<code>` — 依分類瀏覽
- `query.php`（POST）基本檢索：`Access_Num`, `Action_From=search`,
  `Field_Name=kw`, `New_Query=<詞>`, `search_mode=correct_search|like_search|word_like`
- `query.php`（GET）進階檢索：`Action_From=ad_search`, `field1/2/3`,
  `New_Query_a1/a2`, `search_connect`

## 完整分類體系（29 個主題類）
A1土木 A2土地 A3工業 **A4戶口** A5水產業 A6司法 **A7犯罪統計** A8生產總額 A9交通
B1兵事 B2官公吏及恩賞文書 B3林業 B4社寺及宗教 **B5社會事業** B6氣象 B7財政
B8商業金融及貿易 B9專賣 **C1教育** C2理蕃 C3經濟及產業 C4農業 C5團體 C6漁業
**C7衛生** C8糖業 C9警察 D1鑛業 D2其他

## 出版品系列（對本專案最關鍵）
| 代碼 | 系列 |
|---|---|
| BB01 | 臺灣總督府統計書（逐年逐冊，明治30〔1897〕起） |
| **BB07** | **臺灣警察及衛生統計書** |
| BB09 | 犯罪統計書系列（臺灣犯罪統計實…、比較…） |
| **BB17** | **臨時臺灣戶口調查**（殖民地國勢調查） |
| BB1a | 臺灣常住戶口統計 |

## ⚠️ 版權宣告（明確且嚴格）
> 「本資料庫圖文版權為**國立臺灣大學**所有 ©2008 National Taiwan University
> **All Rights Reserved.**」

比省議會的模糊狀態更明確——臺大對**掃描影像與資料庫**主張完整權利。

### 但這次的法律位置反而比省議會好
關鍵差異在「我們要發布什麼」：
- 省議會案：要發布的是**編目員撰寫的描述文字**（是著作）→ 風險高
- 本案：要發布的是**統計表格中的數值**（是事實）→ **事實不受著作權保護**

轉錄統計數字產生的是事實資料集，不是重製臺大的著作。
且底層的 1897–1945 總督府統計書本身早已進入公有領域。
→ **可行性明顯高於省議會軌。**（仍建議在 data paper 中清楚標註影像來源與檢索出處）

## 未解
- `query.php` 直接呼叫回傳首頁（5,633b），未取得結果列表
  → 推測需先取得 session cookie 或填入 `Access_Num`。屬工程細節，非阻斷性
- 尚未取得表格層級 metadata 的實際筆數與欄位

## 附帶發現
`main_browse.php` 連向 **中研院資訊所「台灣統計50年」**
（twstudy.iis.sinica.edu.tw/twstatistic50/）——另一個相關資源，值得列入 D 軌查核。
