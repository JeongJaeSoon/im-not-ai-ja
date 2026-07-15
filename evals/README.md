# Skill evals

`humanize-japanese` のcanonical Agent Skillを実際にモデルへ適用し、レジスター、敬語判断、意味保存を回帰テストするための仕組みです。自然さをモデル自身の主観点だけで採点せず、ケースごとに宣言した契約を決定論的に検証します。評価対象は `skills/humanize-japanese/SKILL.md` と、その相対参照先だけです。

## 構成

- `cases.json`: 入力、文脈、目標レジスター、保護語、保持・除去条件、期待finding ID。
- `result.schema.json`: Claude Code Action が返す構造化出力のJSON Schema。
- `validate_results.py`: 数値、URL、コード、引用、明示的な固有名詞、モダリティ、レジスター、finding IDを検証するゲート。
- `fixtures/reference-results.json`: validator自体をテストする既知の合格結果。
- `.github/workflows/skill-eval.yml`: Claude Code Action v1でskillを実行し、結果とレポートをartifactに保存するworkflow。
- `tests/test_structure.py`: skillを単独directoryへcopyしても相対参照とmetricsが動くことを確認するportable structure test。

現在のケースは、R0/R1/R2/R3、`です・ます`、許可・受益がある/ない`させていただく`、正式通知の`ご了承ください`、敬語の行為者、二重敬語、無修正成功、固有名詞・数値・引用・モダリティの同時保護を含みます。

## ローカル検証

APIを使わず、eval corpusとvalidatorを確認できます。

```bash
python3 evals/validate_results.py \
  --results evals/fixtures/reference-results.json
python3 scripts/validate_repo.py
python3 -m unittest discover -s tests -v
```

## GitHub Actionsの設定

Claude Code公式の対話コマンドでGitHub Appと基本workflowを設定する場合は、repository rootでClaude Codeを起動して次を実行します。

```text
claude
> /install-github-app
```

このrepositoryには独自の `skill-eval` workflowがあるため、model evalの実行には次のrepository secretのどちらか一つを設定します。両方ある場合は `CLAUDE_CODE_OAUTH_TOKEN` を優先します。

Claude Pro、Max、Team、EnterpriseのsubscriptionをCIで使う場合は、Claude Codeで有効期間1年のtokenを発行し、値をコマンドライン引数へ含めず `gh` のpromptへ貼り付けます。

```bash
claude setup-token
gh secret set CLAUDE_CODE_OAUTH_TOKEN --repo JeongJaeSoon/im-not-ai-ja
```

Anthropic API課金を使う場合はAPI keyを設定します。

```bash
gh secret set ANTHROPIC_API_KEY --repo JeongJaeSoon/im-not-ai-ja
```

Actions画面の `skill-eval` → `Run workflow` から手動実行できます。CLIの場合:

```bash
gh workflow run skill-eval.yml \
  --repo JeongJaeSoon/im-not-ai-ja \
  -f model=claude-sonnet-5
```

Pull Requestと`main`へのpushで自動model evalも行う場合は、repository variableを有効にします。

```bash
gh variable set ENABLE_CLAUDE_EVALS \
  --repo JeongJaeSoon/im-not-ai-ja \
  --body true
```

workflowは最初にAgent Skills標準構造、相対参照、eval fixtureをAPIなしで検証します。その後、repositoryの読み取り専用 `GITHUB_TOKEN` をClaude Code Actionへ明示的に渡します。そのため、このevalだけのためにClaude GitHub Appへ他repositoryにも及ぶ広い書き込み権限を付与する必要はありません。fork由来のPull Requestではsecretを渡さず、model evalを実行しません。通常の決定論的テストは常に実行されます。

## モデル選択

既定値は `claude-sonnet-5` です。Sonnet 4.6からのdrop-in upgradeで、日本語リライトと複数ケースのagentic evalに対する能力向上が期待できるためです。回帰比較では `claude-sonnet-4-6`、リリース前の高コストな追加確認では `claude-opus-4-8` を手動選択できます。Sonnet 5はadaptive thinkingを既定で使うため、手動thinking budgetや非既定のsampling parameterは設定しません。

- Claude Code GitHub Actions: https://code.claude.com/docs/en/github-actions
- Claude Code authentication: https://code.claude.com/docs/en/iam
- Claude model overview: https://platform.claude.com/docs/en/about-claude/models/overview
- Claude Sonnet 5: https://platform.claude.com/docs/en/about-claude/models/whats-new-sonnet-5

## 合否

全ケースが次を満たした場合だけ成功します。

1. 目標レジスターが一致する。
2. 数値、URL、コード、引用、明示的な固有名詞が保たれる。
3. 否定、可能、義務、条件のカテゴリが変わらない。
4. ケースの保持・除去条件と期待finding IDを満たす。
5. 自己検証が全項目trueで、gradeがAまたはBである。
6. 長文の変更率がケースの上限以内である。短文は変更率を参考値にする。

出力本文、ケース別エラー、変更率、contract integrityは14日間のartifactとして保存されます。OAuth tokenとAPI keyはartifactやpromptへ書き込みません。

このmodel evalの実行ホストはClaude Codeですが、評価対象はランタイム固有のClaude版ではなくcanonical Agent Skillです。Codex互換性は、skill directoryを単独でcopyしても相対参照が解決すること、skillが特定製品の配置やツール名を必須にしないことをCIで保証します。
