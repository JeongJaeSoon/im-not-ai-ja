# Humanize JA — 日本語の「AIっぽさ」を整える

> [!IMPORTANT]
> このリポジトリは [epoko77-ai/im-not-ai](https://github.com/epoko77-ai/im-not-ai) の設計に着想を得て作った独立した日本語版です。GitHubのfork機能は使っていません。原著作権表示とMIT Licenseを引き継ぎ、変更点と参考資料を [NOTICE.md](NOTICE.md) に記録しています。

AIが下書きした日本語の意味を変えず、文体、リズム、語彙、読み手との距離を用途に合う形へ整えるポータブルな [Agent Skill](https://agentskills.io/specification) です。Claude CodeとCodexは、同じ `SKILL.md` と同じ補助ファイルを使います。

## 構造

スキル本体は一つだけです。

```text
skills/humanize-japanese/
├── SKILL.md              必須の指示と実行契約
├── references/           必要時だけ読む日本語規則と分類体系
├── scripts/metrics.py    任意の計量・before/after検査
└── assets/baseline.json  metrics.pyの既定閾値
```

リポジトリ直下の `skills/` は、GitHub上でスキルを配布・発見するためのパッケージ階層です。実際にインストールされる単位は、その内側の `humanize-japanese/` です。ランタイム別のskillコピー、adapter symlink、plugin manifest、bundled agent定義は持ちません。

## 日本語レジスターを消さない

`です・ます`や敬語はAIの証拠ではありません。話し手、読み手、媒体、行為者に合っているかを確認します。

| レジスター | 例 | 主な用途 |
|---|---|---|
| R0 親しい会話体 | `だよ`、`だね`、`じゃん` | 友人、家族、個人チャット |
| R1 中立的な常体 | `だ`、`である` | 学術、報道、仕様、評論 |
| R2 中立的な丁寧体 | `です`、`ます` | ブログ、案内、一般メール |
| R3 ビジネス丁寧体 | `いたします`、`申し上げます` | 顧客対応、社外文書 |
| R4 儀礼・高度配慮 | 謙譲語、尊敬語、定型挨拶 | 式辞、謝罪、重要な依頼 |

`させていただきます`は一律に削除しません。相手の許可を受け、自分側が恩恵を得る行為なら保持します。`ご了承ください`も、制約の受容を求める正式通知なら残し、友人向けの文章や一方的な免責で距離が浮く場合だけ調整します。

## 主な機能

- 日本語固有の10カテゴリ・59パターンをS1 / S2 / S3とGuardで整理
- R0〜R4、尊敬語・謙譲語、`させていただく`、`ご了承ください`を文脈で判断
- Fastでは診断、最小編集、自己検証を一回で実施
- Strictではdetector、rewriter、fidelity audit、naturalness reviewを順に実施
- 数値、日付、固有名詞、引用、コード、URL、モダリティ、因果を保護
- 文長CV、読点密度、文末反復、接続詞、定型句を任意の補助scriptで診断

## インストール

まずrepositoryをcloneします。

```bash
git clone https://github.com/JeongJaeSoon/im-not-ai-ja.git
cd im-not-ai-ja
```

Claude Codeの標準user skill path:

```bash
mkdir -p ~/.claude/skills
ln -s "$(pwd)/skills/humanize-japanese" ~/.claude/skills/humanize-japanese
```

Codexの標準user skill path:

```bash
mkdir -p ~/.agents/skills
ln -s "$(pwd)/skills/humanize-japanese" ~/.agents/skills/humanize-japanese
```

project単位では、Claude Codeは `.claude/skills/humanize-japanese`、Codexは `.agents/skills/humanize-japanese` に同じskill directoryをlinkまたはcopyします。

任意のcross-agent installerを使う場合:

```bash
npx skills add JeongJaeSoon/im-not-ai-ja \
  --skill humanize-japanese \
  --global \
  --agent claude-code \
  --agent codex \
  --yes
```

copy mode、更新、削除、旧構成からの移行は [INSTALL.md](INSTALL.md) を参照してください。

## 使い方

```text
この文章を humanize-japanese で自然にして。意味と敬語レベルは変えないで。

この社外メールを整えて。させていただきますが本当に必要な箇所だけ残して。

この友人向けメッセージのAIっぽさを消して。です・ます調にはしないで。

この論文草稿を --strict で確認して。である調と専門用語は維持して。
```

## Eval

`evals/cases.json` には、R0〜R3、`です・ます`、`させていただく`、`ご了承ください`、敬語の行為者、固有名詞・数値・引用・モダリティ保護を含む回帰ケースがあります。

GitHub Actionsの `skill-eval` は、Claude Code Actionでこの単一スキルを実行し、構造化結果を決定論的なvalidatorへ渡します。設定とモデル選択は [evals/README.md](evals/README.md) を参照してください。

## 設計原則

1. 事実、主張、否定、可能性、義務、因果、数値、固有名詞、引用を変えない。
2. 丁寧さの量だけをAI tellにしない。用途と関係性を先に判定する。
3. 一つの語句だけでAIと断定せず、反復、共起、文書全体の偏りを見る。
4. 体験、感情、固有名詞、出典を勝手に追加して「人間らしさ」を捏造しない。
5. AI検出器の回避を保証しない。目的は日本語の品質改善であり、著者性の偽装ではない。

## ライセンス

MIT License。原プロジェクトの著作権表示を保持しています。詳細は [LICENSE](LICENSE) と [NOTICE.md](NOTICE.md) を参照してください。
