# Installation

## 自動インストール

```bash
git clone https://github.com/JeongJaeSoon/im-not-ai-ja.git
cd im-not-ai-ja
./install.sh
```

`install.sh` は利用できる CLI を検出し、リポジトリ内のスキルへシンボリックリンクを作ります。

```bash
./install.sh --claude-only
./install.sh --codex-only
./install.sh --gemini-only
./install.sh --copy
./install.sh --dry-run
```

## 手動インストール

### Claude Code

```bash
mkdir -p ~/.claude/skills
ln -s "$(pwd)/.claude/skills/humanize-japanese" ~/.claude/skills/humanize-japanese
```

Claude Code の plugin marketplace から使う場合:

```text
/plugin marketplace add JeongJaeSoon/im-not-ai-ja
/plugin install humanize-japanese@im-not-ai-ja
```

### Codex

```bash
mkdir -p ~/.codex/skills
ln -s "$(pwd)/codex/skills/humanize-japanese" ~/.codex/skills/humanize-japanese
```

### Gemini CLI

```bash
gemini extensions link "$(pwd)"
```

## アンインストール

```bash
./uninstall.sh
```

スクリプトは、このリポジトリを指すシンボリックリンクだけを削除します。`--copy` で入れたファイルは手動で削除してください。
