# Skill evals

`humanize-japanese` を実際にモデルへ適用し、レジスター、敬語判断、意味保存を回帰テストするための仕組みです。自然さをモデル自身の主観点だけで採点せず、ケースごとに宣言した契約を決定論的に検証します。

## 構成

- `cases.json`: 入力、文脈、目標レジスター、保護語、保持・除去条件、期待finding ID。
- `result.schema.json`: Claude Code Action が返す構造化出力のJSON Schema。
- `validate_results.py`: 数値、URL、コード、引用、明示的な固有名詞、モダリティ、レジスター、finding IDを検証するゲート。
- `fixtures/reference-results.json`: validator自体をテストする既知の合格結果。
- `.github/workflows/skill-eval.yml`: Claude Code Action v1でskillを実行し、結果とレポートをartifactに保存するworkflow。

現在のケースは、R0/R1/R2/R3、`です・ます`、許可・受益がある/ない`させていただく`、正式通知の`ご了承ください`、敬語の行為者、二重敬語、無修正成功、固有名詞・数値・引用・モダリティの同時保護を含みます。

## ローカル検証

APIを使わず、eval corpusとvalidatorを確認できます。

```bash
python3 evals/validate_results.py \
  --results evals/fixtures/reference-results.json
python3 -m unittest discover -s tests -v
```

## GitHub Actionsの設定

Claude APIを使うmodel evalにはrepository secretが必要です。

```bash
gh secret set ANTHROPIC_API_KEY --repo JeongJaeSoon/im-not-ai-ja
```

Actions画面の `skill-eval` → `Run workflow` から手動実行できます。CLIの場合:

```bash
gh workflow run skill-eval.yml \
  --repo JeongJaeSoon/im-not-ai-ja \
  -f model=claude-sonnet-4-6
```

Pull Requestと`main`へのpushで自動model evalも行う場合は、repository variableを有効にします。

```bash
gh variable set ENABLE_CLAUDE_EVALS \
  --repo JeongJaeSoon/im-not-ai-ja \
  --body true
```

fork由来のPull Requestではsecretを渡さず、model evalを実行しません。通常の決定論的テストは常に実行されます。

## モデル選択

既定値は `claude-sonnet-4-6` です。日本語リライトと複数ケースのツール読み取りに十分な品質があり、継続的なevalで速度とコストのバランスを取りやすいためです。リリース前の追加確認では手動実行時に `claude-opus-4-8` を選べます。

- Claude Code GitHub Actions: https://code.claude.com/docs/en/github-actions
- Claude model overview: https://platform.claude.com/docs/en/about-claude/models/overview

## 合否

全ケースが次を満たした場合だけ成功します。

1. 目標レジスターが一致する。
2. 数値、URL、コード、引用、明示的な固有名詞が保たれる。
3. 否定、可能、義務、条件のカテゴリが変わらない。
4. ケースの保持・除去条件と期待finding IDを満たす。
5. 自己検証が全項目trueで、gradeがAまたはBである。
6. 長文の変更率がケースの上限以内である。短文は変更率を参考値にする。

出力本文、ケース別エラー、変更率、contract integrityは14日間のartifactとして保存されます。API keyはartifactやpromptへ書き込みません。
