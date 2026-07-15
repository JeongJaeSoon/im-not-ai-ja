# Humanize JA — 文脈を保ち、日本語の「AIっぽさ」を整える

AIが下書きした日本語を、内容や事実、読み手との距離感を保ったまま推敲するポータブルな [Agent Skill](https://agentskills.io/specification) です。Claude CodeとCodexは、同じ `SKILL.md` と同じ補助ファイルを使います。

単語を機械的に置き換えるのではなく、主語の省略、文末、敬語、漢語・和語・カタカナ語の配分、接続、文のリズムまで文脈に沿って確認します。

## 日本語のレジスターを保つ

`です・ます`や敬語は、それだけでAIらしさの根拠にはなりません。話し手、読み手、媒体、行為者に合っているかを確認します。

| レジスター | 例 | 主な用途 |
|---|---|---|
| R0 親しい会話体 | `だよ`、`だね`、`じゃん` | 友人、家族、個人チャット |
| R1 中立的な常体 | `だ`、`である` | 学術、報道、仕様、評論 |
| R2 中立的な丁寧体 | `です`、`ます` | ブログ、案内、一般メール |
| R3 ビジネス丁寧体 | `いたします`、`申し上げます` | 顧客対応、社外文書 |
| R4 儀礼・高度配慮 | 謙譲語、尊敬語、定型挨拶 | 式辞、謝罪、重要な依頼 |

`させていただきます`は一律に削除しません。相手または第三者の許可を受け、自分側が恩恵を得る行為なら保持します。`ご了承ください`も、制約の受容を求める正式な通知なら残し、友人向けの文章や一方的な免責で距離が浮く場合だけ調整します。

## 主な機能

- 日本語固有の10カテゴリ・59パターンをS1 / S2 / S3とGuardで整理
- R0〜R4、尊敬語・謙譲語、`させていただく`、`ご了承ください`を文脈で判断
- Fastモードでは診断、最小限の編集、自己検証を一回で実施
- Strictモードでは検出、書き換え、内容保存の監査、自然さのレビューを順に実施
- 数値、日付、固有名詞、引用、コード、URL、モダリティ、因果関係を保護
- 文長の変動係数、読点密度、文末反復、接続詞、定型句を任意の補助スクリプトで診断

## インストール

Claude CodeとCodexのどちらでも、同じ名前のマーケットプレイスとプラグインを登録します。リポジトリのクローンやシンボリックリンクは不要です。

### Claude Code

```bash
claude plugin marketplace add JeongJaeSoon/im-not-ai-ja
claude plugin install humanize-japanese@im-not-ai-ja
```

インストール後は、自然な文章で依頼するか、`/humanize-japanese:humanize-japanese` と明示して呼び出せます。反映されない場合はClaude Codeを再起動するか、`/reload-plugins`を実行してください。

### Codex

```bash
codex plugin marketplace add JeongJaeSoon/im-not-ai-ja
codex plugin add humanize-japanese@im-not-ai-ja
```

インストール後は、自然な文章で依頼するか、`$humanize-japanese:humanize-japanese` と明示して呼び出せます。追加が反映されない場合はCodexを再起動してください。

更新、削除、ローカル開発用の直接インストールは [INSTALL.md](INSTALL.md) を参照してください。

### 代替: 共通スキルインストーラー

プラグイン機能を使えない環境では、[skills CLI](https://github.com/vercel-labs/skills) で同じスキル本体を直接インストールできます。これはClaude CodeやCodexの公式プラグイン機能ではありません。

```bash
npx skills add JeongJaeSoon/im-not-ai-ja \
  --skill humanize-japanese \
  --global \
  --agent claude-code \
  --agent codex \
  --yes
```

## 使い方

自然な日本語で依頼できます。

```text
この文章を humanize-japanese で自然にして。意味と敬語レベルは変えないで。

この社外メールを整えて。「させていただきます」が本当に必要な箇所だけ残して。

この友人向けメッセージのAIっぽさを消して。です・ます調にはしないで。

この論文草稿を --strict で確認して。である調と専門用語は維持して。

書き換えず、気になる箇所だけ --diagnose-only で指摘して。
```

## スキルの構成

プラグインとして配布しますが、実際のスキル本体は一つだけです。

```text
im-not-ai-ja/
├── .claude-plugin/      Claude Code用のプラグイン・マーケットプレイス定義
├── .codex-plugin/       Codex用のプラグイン定義
├── .agents/plugins/     Codex用のマーケットプレイス定義
└── skills/
    └── humanize-japanese/
        ├── SKILL.md              中核となる指示と実行契約
        ├── references/           日本語の規則、分類体系、書き換え指針
        ├── scripts/metrics.py    任意の計量診断とbefore/after検査
        └── assets/baseline.json  metrics.pyが使う既定の閾値
```

`.claude-plugin/plugin.json` と `.codex-plugin/plugin.json` は、どちらも同じ `skills/` を参照します。ランタイム別のスキルコピー、アダプター用シンボリックリンク、同梱エージェント定義は持ちません。

通常の推敲にPythonは必要ありません。`metrics.py`は計量診断や厳密な変更前後の比較が必要な場合だけ使う選択的な補助ツールです。リポジトリ直下の `scripts/` と `evals/` は開発・CI用であり、スキル本体としてインストールされません。

## 評価

`evals/cases.json` には、R0〜R3、`です・ます`、許可・受益がある場合とない場合の`させていただく`、正式通知の`ご了承ください`、敬語の行為者、固有名詞、数値、引用、モダリティ保護を含む回帰ケースがあります。

GitHub Actionsの `skill-eval` は、Claude Code Actionで共通のスキル本体を実行し、構造化された結果を決定論的な検証スクリプトへ渡します。モデルの主観だけで自然さを採点せず、レジスターと内容保存の契約をケース単位で検証します。設定とモデル選択は [evals/README.md](evals/README.md) を参照してください。

## 設計原則

1. 事実、主張、否定、可能性、義務、因果、数値、固有名詞、引用を変えない。
2. 丁寧さの量だけをAIらしさの根拠にしない。用途と関係性を先に判断する。
3. 一つの語句だけでAIと断定せず、反復、共起、文書全体の偏りを見る。
4. 体験、感情、固有名詞、出典を勝手に追加して「人間らしさ」を捏造しない。
5. AI検出器の回避を保証しない。目的は日本語の品質改善であり、著者性の偽装ではない。

## 既存プロジェクトとの関係

日本語向けの文章推敲ツールは、すでに複数公開されています。本プロジェクトは、それらが存在しないことを前提にしていません。

| プロジェクト | 参照した観点 |
|---|---|
| [gonta223/humanizer-ja](https://github.com/gonta223/humanizer-ja) | 主語の過剰明示、文体の均一性 |
| [iKora128/stop-ai-slop-jp](https://github.com/iKora128/stop-ai-slop-jp) | 無生物主語による不自然な行為者表現（false agency）、書き手の立場、構成を先に整える編集 |
| [makotofalcon/humanizer-ja](https://github.com/makotofalcon/humanizer-ja) | 漢語の連鎖、翻訳調のカタカナ語 |
| [yourbright-jp/humanizer-jp](https://github.com/yourbright-jp/humanizer-jp) | 文長の変動係数、句読点、レジスター由来の交絡 |

各プロジェクトの規則をそのまままとめたものではありません。反例と日本語の用途差を照合し、このプロジェクトの分類体系として再構成しています。参照したリビジョン、ライセンス、研究資料は [NOTICE.md](NOTICE.md) に記録しています。

## 由来と帰属

このプロジェクトは [epoko77-ai/im-not-ai](https://github.com/epoko77-ai/im-not-ai) に着想を得た、日本語向けの独立プロジェクトとして始まりました。初期のFast / Strictワークフロー、重大度に基づくレビュー、最小編集、内容保存の考え方から影響を受けています。

現在の日本語分類体系、R0〜R4のレジスター設計、敬語処理、ポータブルAgent Skillの実装、評価基盤、インストール構成は、このリポジトリで独自に開発しています。GitHubのfork機能は使っていません。詳細は [NOTICE.md](NOTICE.md) を参照してください。

## ライセンス

MIT Licenseです。プロジェクトの出発点と初期設計への影響を明示するため、原プロジェクトの著作権表示を保持しています。詳細は [LICENSE](LICENSE) と [NOTICE.md](NOTICE.md) を参照してください。
