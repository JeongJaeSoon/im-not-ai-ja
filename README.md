# Humanize JA — 日本語の「AIっぽさ」を整える

> [!IMPORTANT]
> このリポジトリは [epoko77-ai/im-not-ai](https://github.com/epoko77-ai/im-not-ai) の設計とソース構成に着想を得て作った、独立した日本語版です。GitHub の fork 機能は使っていません。原著作権表示と MIT License を引き継ぎ、変更点と追加の参考資料を [NOTICE.md](NOTICE.md) に記録しています。

AI が下書きした日本語の意味を変えず、文体・リズム・語彙・距離感を用途に合う形へ整える Claude Code / Codex 向け Agent Skill です。単語を機械的に置き換えるのではなく、日本語固有の省略、文末、敬語、漢語・和語・カタカナ語の配分まで確認します。

## 既存プロジェクトとの関係

日本語向け humanizer はすでに存在します。本プロジェクトは「日本語版がない」ことを前提にしていません。

| プロジェクト | 強み | 本プロジェクトでの扱い |
|---|---|---|
| [yourbright-jp/humanizer-jp](https://github.com/yourbright-jp/humanizer-jp) | 人間・Claude 各1,105記事の計量比較 | 文長 CV、句読点、文末分析の研究結果を参照 |
| [iKora128/stop-ai-slop-jp](https://github.com/iKora128/stop-ai-slop-jp) | 立場・主体・構造を優先する編集 | false agency、書き手不在の観点を参照 |
| [gonta223/humanizer-ja](https://github.com/gonta223/humanizer-ja) | 日本語固有の20パターン | 主語の過剰明示、文体の均一性を参照 |
| [makotofalcon/humanizer-ja](https://github.com/makotofalcon/humanizer-ja) | 英語版 humanizer の日本語適応 | 漢語連鎖、翻訳調カタカナの観点を参照 |

本プロジェクトの違いは、`im-not-ai` 型の Fast / Strict ワークフロー、スパン単位の重大度、意味保存監査、決定論的な計量スクリプト、Codex 対応、そして日本語のレジスターを独立した制約として扱う点です。

## 日本語レジスターを消さない

`です・ます`や敬語は AI の証拠ではありません。話し手と読み手の関係に合っているかを見ます。

| レジスター | 例 | 主な用途 |
|---|---|---|
| 親しい会話体 | `だよ`、`だね`、`じゃん` | 友人同士、個人チャット |
| 中立的な丁寧体 | `です`、`ます` | ブログ、説明、一般メール |
| ビジネス丁寧体 | `いたします`、`申し上げます` | 顧客対応、社外文書 |
| 配慮・謙譲表現 | `させていただきます`、`ご了承ください` | 許可・受益・事前合意がある場面 |
| 常体 | `だ`、`である` | 学術、報道、仕様、評論 |

たとえば `させていただきます` は一律削除しません。相手の許可を受け、自分が恩恵を得る行為なら妥当です。単に `実施します` で足りるのに儀礼的に連発している場合だけ候補にします。`ご了承ください` も、相手に不利益を受け入れてもらう通知なら残し、友人向けの文章や一方的な免責で浮いている場合は調整します。

## 主な機能

- 日本語固有の 10 カテゴリ・59 パターンを S1 / S2 / S3 で分類
- 文長変動係数、読点密度、文字種、文末反復、接続詞、定型句を依存なしで計測
- Fast: 一回の編集で検出・書き換え・自己検証
- Strict: detector → rewriter → fidelity auditor → naturalness reviewer
- 原文の数値、固有名詞、引用、モダリティ、敬語レベルを保護
- Claude Code、Codex CLI、Gemini CLI 用の構成を同梱

## インストール

```bash
git clone https://github.com/JeongJaeSoon/im-not-ai-ja.git
cd im-not-ai-ja
./install.sh
```

- Claude Code: `/humanize-japanese`
- Codex: `$humanize-japanese`
- Gemini CLI: `/humanize-japanese`

詳細は [INSTALL.md](INSTALL.md) を参照してください。

## 使い方

```text
この文章を humanize-japanese で自然にして。意味と敬語レベルは変えないで。

この社外メールを整えて。させていただきますが本当に必要な箇所だけ残して。

この友人向けメッセージのAIっぽさを消して。です・ます調にはしないで。

この論文草稿を --strict で確認して。である調と専門用語は維持して。
```

診断だけ実行することもできます。

```bash
python3 .claude/skills/humanize-japanese/scripts/metrics.py draft.md
python3 .claude/skills/humanize-japanese/scripts/metrics.py before.md --compare after.md
python3 .claude/skills/humanize-japanese/scripts/metrics.py before.md --compare after.md \
  --protect "人名" --protect "製品名"
```

## 設計原則

1. 意味を変えない。主張、否定、可能性、義務、因果、数値、固有名詞、引用を保存する。
2. 形式的な丁寧さを AI tell と決めつけない。用途と関係性を先に判定する。
3. 一つの語句だけで AI と断定しない。反復、共起、文書全体の偏りで判断する。
4. 「人間らしさ」を捏造しない。体験、感情、固有名詞、出典を勝手に追加しない。
5. AI 検出器の回避を保証しない。目的は日本語の品質改善であり、著者性の偽装ではない。

## Skill eval

`evals/cases.json` に、R0〜R3、`です・ます`、`させていただく`、`ご了承ください`、敬語の行為者、固有名詞・数値・引用・モダリティ保護を含む回帰ケースがあります。

通常のCIではAPI不要のvalidatorとfixtureを実行します。GitHub Actionsの `skill-eval` workflowを手動実行すると、`anthropics/claude-code-action@v1` が既定の `claude-sonnet-4-6` で実際にskillを使い、構造化された結果を決定論的な契約検査へ渡します。設定方法、コスト制御、自動PR evalの有効化は [evals/README.md](evals/README.md) を参照してください。

## ライセンスとクレジット

MIT License。原プロジェクトの著作権表示を保持しています。参考プロジェクトと研究資料、取り込んだ設計上の影響は [NOTICE.md](NOTICE.md) に記載しています。
