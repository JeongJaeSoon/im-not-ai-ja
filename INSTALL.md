# Installation

Claude CodeとCodexは、どちらも同じ `skills/humanize-japanese/` を含むプラグインをインストールします。実行環境別のスキル本文やエージェント定義はありません。

## 1. Claude Code

マーケットプレイスを登録し、プラグインをインストールします。

```bash
claude plugin marketplace add JeongJaeSoon/im-not-ai-ja
claude plugin install humanize-japanese@im-not-ai-ja
```

新しいセッションで自然な文章で依頼するか、`/humanize-japanese:humanize-japanese` と明示して実行します。反映されない場合は `/reload-plugins` を実行するか、Claude Codeを再起動してください。

更新:

```bash
claude plugin marketplace update im-not-ai-ja
claude plugin update humanize-japanese@im-not-ai-ja
```

削除:

```bash
claude plugin uninstall humanize-japanese@im-not-ai-ja
```

公式資料: [Claude Code plugins](https://code.claude.com/docs/en/plugins)、[Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)

## 2. Codex

同じリポジトリをマーケットプレイスとして登録し、同じ名前のプラグインをインストールします。

```bash
codex plugin marketplace add JeongJaeSoon/im-not-ai-ja
codex plugin add humanize-japanese@im-not-ai-ja
```

新しいセッションで自然な文章で依頼するか、`$humanize-japanese:humanize-japanese` と明示して実行します。反映されない場合はCodexを再起動してください。

更新:

```bash
codex plugin marketplace upgrade im-not-ai-ja
codex plugin remove humanize-japanese@im-not-ai-ja
codex plugin add humanize-japanese@im-not-ai-ja
```

削除:

```bash
codex plugin remove humanize-japanese@im-not-ai-ja
```

公式資料: [Plugins in Codex](https://help.openai.com/en/articles/20001256-plugins-in-codex)

## 3. 代替: 共通スキルインストーラー

プラグイン機能を使えない環境では、[skills CLI](https://github.com/vercel-labs/skills) で両方へスキル本体を直接インストールできます。Claude CodeやCodexの公式プラグイン機能ではありません。

```bash
npx skills add JeongJaeSoon/im-not-ai-ja \
  --skill humanize-japanese \
  --global \
  --agent claude-code \
  --agent codex \
  --yes
```

skills CLIで入れた場合の更新と削除:

```bash
npx skills update humanize-japanese --global --yes
npx skills remove humanize-japanese \
  --global \
  --agent claude-code \
  --agent codex \
  --yes
```

## 4. ローカル開発

未公開の変更を試す場合だけリポジトリをクローンし、各実行環境のスキル配置先へシンボリックリンクできます。通常の利用ではこの手順は不要です。

```bash
git clone https://github.com/JeongJaeSoon/im-not-ai-ja.git
cd im-not-ai-ja
mkdir -p ~/.claude/skills ~/.agents/skills
ln -s "$(pwd)/skills/humanize-japanese" ~/.claude/skills/humanize-japanese
ln -s "$(pwd)/skills/humanize-japanese" ~/.agents/skills/humanize-japanese
```

プラグイン版と直接インストール版を同時に有効にすると、同じスキルが重複して見える場合があります。動作確認が終わったら、自分が作成したリンクであることを `readlink` で確認して削除してください。

```bash
unlink ~/.claude/skills/humanize-japanese
unlink ~/.agents/skills/humanize-japanese
```

## 5. パッケージの開発者向け検証

Claude Codeのマニフェストとマーケットプレイスは公式validatorで検証できます。

```bash
claude plugin validate . --strict
```

Codexは隔離した一時的な `CODEX_HOME` で、実際の登録とインストールを確認できます。

```bash
export CODEX_HOME="$(mktemp -d)"
codex plugin marketplace add ./ --json
codex plugin add humanize-japanese@im-not-ai-ja --json
codex plugin list --json
```

リポジトリ共通の構造、バージョン同期、単一 `SKILL.md`、評価コーパスは次のコマンドで検証します。

```bash
python3 scripts/validate_repo.py
python3 -m unittest discover -s tests -v
python3 evals/validate_results.py \
  --results evals/fixtures/reference-results.json
```

## 6. 旧構成からの移行

以前のバージョンで `.claude/skills/`、`.agents/skills/`、`.codex/skills/`、`codex/skills/`、または `agents/` へのリンクやコピーを作った場合は、それが自分で追加したものか確認してから削除し、プラグインとして入れ直してください。同名の直接スキルとプラグインスキルを同時に有効にしないでください。
