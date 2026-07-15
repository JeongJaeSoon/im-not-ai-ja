---
name: humanize-japanese
description: AIで下書きした日本語を、意味・数値・引用・モダリティ・敬語レベルを保って自然に推敲する。主語省略、文末、丁寧体/常体、尊敬語・謙譲語、させていただく、ご了承ください、漢語・カタカナ語、接続詞、リズム、定型句を診断する。「AIっぽさを消して」「自然な日本語に」「敬語を保って」「humanize Japanese」で使う。
---

# Humanize Japanese for Codex

1. `references/quick-rules.md` を読む。
2. 読者、媒体、ジャンル、R0〜R4のレジスターを推定する。
3. 敬語・会話体・社外文書なら `references/register-guide.md` も読む。
4. 数値、固有名詞、引用、モダリティ、因果、レジスターを固定する。
5. taxonomy IDが付く箇所だけ、S1→S2の順に最小編集する。
6. `scripts/metrics.py` は5文以上の補助診断にだけ使う。
7. 自己検証6項目を通し、変更率30%超で警告、50%超で中止する。

Strictまたは理由説明では `references/ai-tell-taxonomy.md` と `references/rewriting-playbook.md` を読む。`です・ます`や敬語の多さをAI判定に使わない。`させていただく`は許可と受益、`ご了承ください`は制約受容の通知かを確認する。

出力は、状態一行、推敲本文、主なfinding、保持した表現の理由、不確実箇所の順にする。原文にない体験・出典・具体例を足さない。AI検出器回避を保証しない。
