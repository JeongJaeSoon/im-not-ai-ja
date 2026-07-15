# Installation

Claude CodeとCodexは、どちらも同じ `skills/humanize-japanese/` をインストールします。ランタイム別のskill本文やagent定義はありません。

## 1. Repositoryを取得する

```bash
git clone https://github.com/JeongJaeSoon/im-not-ai-ja.git
cd im-not-ai-ja
```

## 2. Claude Codeの標準path

Claude Codeの公式skill locationは次のとおりです。

- User scope: `~/.claude/skills/humanize-japanese/SKILL.md`
- Project scope: `<project>/.claude/skills/humanize-japanese/SKILL.md`

User scopeへsymlinkする場合:

```bash
mkdir -p ~/.claude/skills
ln -s "$(pwd)/skills/humanize-japanese" ~/.claude/skills/humanize-japanese
```

Project scopeへsymlinkする場合は、対象projectのrootで実行します。

```bash
mkdir -p .claude/skills
ln -s "/absolute/path/to/im-not-ai-ja/skills/humanize-japanese" \
  .claude/skills/humanize-japanese
```

新しいClaude Code sessionで `/humanize-japanese` を実行します。追加が反映されない場合はsessionを再起動してください。

公式資料: [Claude Code skills](https://code.claude.com/docs/en/skills)

## 3. Codexの標準path

Codexの公式skill locationは次のとおりです。

- User scope: `~/.agents/skills/humanize-japanese/SKILL.md`
- Repository scope: `<project>/.agents/skills/humanize-japanese/SKILL.md`

User scopeへsymlinkする場合:

```bash
mkdir -p ~/.agents/skills
ln -s "$(pwd)/skills/humanize-japanese" ~/.agents/skills/humanize-japanese
```

Repository scopeへsymlinkする場合は、対象repositoryのrootで実行します。

```bash
mkdir -p .agents/skills
ln -s "/absolute/path/to/im-not-ai-ja/skills/humanize-japanese" \
  .agents/skills/humanize-japanese
```

新しいCodex sessionで `$humanize-japanese` を指定するか、`/skills` で一覧を確認します。追加が反映されない場合はCodexを再起動してください。

公式資料: [Codex skills](https://developers.openai.com/codex/skills)

## 4. Copy mode

symlinkを使えない場合はskill directory全体をcopyします。

```bash
cp -R skills/humanize-japanese ~/.claude/skills/humanize-japanese
cp -R skills/humanize-japanese ~/.agents/skills/humanize-japanese
```

copy modeでは二つの独立したcopyができるため、更新時に両方を入れ直してください。symlink modeではこのrepositoryで `git pull --ff-only` すれば両方へ反映されます。

## 5. 任意のcross-agent installer

Claude CodeやCodexの公式機能ではありませんが、[skills CLI](https://github.com/vercel-labs/skills) を使うと両方へ同時に入れられます。

```bash
npx skills add JeongJaeSoon/im-not-ai-ja \
  --skill humanize-japanese \
  --global \
  --agent claude-code \
  --agent codex \
  --yes
```

symlinkを使えない環境では `--copy` を追加します。

skills CLIで入れた場合の更新と削除:

```bash
npx skills update humanize-japanese --global --yes
npx skills remove humanize-japanese \
  --global \
  --agent claude-code \
  --agent codex \
  --yes
```

## 6. 旧構成からの移行

以前のversionでrepository内の `.claude/skills/`、`.codex/skills/`、`codex/skills/`、または `agents/` を直接参照するlinkを作った場合、そのlinkは純粋なAgent Skill構成への移行後には使いません。`readlink` で自分の旧linkであることを確認して削除し、このページの標準pathへ入れ直してください。

Claude Code plugin marketplace版を入れていた場合も、旧pluginを無効化または削除してからAgent Skillとして入れ直します。同名の旧plugin skillと新しいuser skillを同時に有効にしないでください。

## 7. 手動アンインストール

symlink modeの場合は、自分が作成したlinkであることを `readlink` で確認してから削除します。

```bash
unlink ~/.claude/skills/humanize-japanese
unlink ~/.agents/skills/humanize-japanese
```

copy modeの場合は、必要なファイルを退避した後、各copyを手動で削除してください。
