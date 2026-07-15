---
name: humanize-redo
description: humanize-japaneseの直近結果を、指定カテゴリ・段落・強度・レジスター指示に沿って再推敲する。「もう一度」「この段落だけ」「敬語だけ戻して」「AI表現をさらに減らして」で使う。
---

# Humanize Redo

1. `_workspace/` の最新runを特定する。
2. 前回の `final.md` と `summary.md` を読む。
3. ユーザーが指定したfindingだけ再処理する。
4. 原文 `01_input.txt` と再照合し、累積変更率を計算する。
5. レジスターを前回より勝手に移動しない。
6. 最大3 roundで止め、残る問題を報告する。
