# Notices and attribution

## Origin and current relationship

This project began as an independent Japanese adaptation inspired by:

- `epoko77-ai/im-not-ai` — https://github.com/epoko77-ai/im-not-ai
- Upstream revision inspected during initial implementation: `14aeb52d13e737beb4e999cb7cb92275d0969689`
- License: MIT
- Copyright: `Copyright (c) 2026 epoko77-ai`

The upstream project informed the initial Fast / Strict workflow, severity-based review, minimum-editing principle, and content-fidelity contract. Its detector–rewriter–auditor idea remains a workflow influence, but the current repository implements those responsibilities as phases inside one portable skill rather than as copied or bundled agents.

The current Japanese taxonomy, R0–R4 register model, honorific handling, metrics, evaluation system, portable Agent Skill implementation, and installation layout are developed independently in this repository. No upstream runtime adapter, agent definition, command, plugin manifest, or package layout is used by the current implementation.

This repository is not a GitHub fork. The upstream copyright notice and MIT License are preserved in `LICENSE` to document the project's origin and the design influence retained from its initial implementation.

## Japanese open-source references

The Japanese taxonomy was designed after comparing these projects:

- `gonta223/humanizer-ja` — https://github.com/gonta223/humanizer-ja — revision `a1e343696e43aa50e7218891f3319ab22cde3464` — MIT, Copyright (c) 2025 Siqi Chen and Copyright (c) 2026 SuguruKun_ai. Consulted for explicit-subject and uniform-style observations.
- `iKora128/stop-ai-slop-jp` — https://github.com/iKora128/stop-ai-slop-jp — revision `e09d32796f253a62693885757cea484c275d06f2` — MIT, Copyright (c) 2026 Daichi Nagashima. Consulted for false agency, authorial stance, and structure-first editing.
- `makotofalcon/humanizer-ja` — https://github.com/makotofalcon/humanizer-ja — revision `4cc01cdd5aff4102888e9396c3ba16da99828f78` — MIT, Copyright (c) 2025. Consulted for kanji-compound chains and translation-like katakana usage.
- `yourbright-jp/humanizer-jp` — https://github.com/yourbright-jp/humanizer-jp — revision `e252b87c39270a0b9359c1e1e1f8d48b710ff4de` — MIT, Copyright (c) 2026 yourbright-jp. Consulted for sentence-length CV, punctuation, and register-confound findings.

No corpus data from these repositories is redistributed here. Rules were reconciled and rewritten for this project; empirical findings take precedence where heuristic projects disagree.

## Portable Agent Skill packaging references

The canonical `skills/humanize-japanese/` layout and installation documentation were checked against the Agent Skills specification and these public repositories. They were consulted for interoperability conventions; no skill content was copied from them.

- Agent Skills specification — https://agentskills.io/specification. Used as the normative structure: `SKILL.md` with optional `references/`, `scripts/`, and `assets/`.
- `freee/freee-mcp` — https://github.com/freee/freee-mcp — revision `f488b18f4de95778147357cbc13ac750e6abe58f`. Consulted for maintaining one canonical `skills/` tree across clients.
- `anthropics/skills` — https://github.com/anthropics/skills — revision `9d2f1ae187231d8199c64b5b762e1bdf2244733d`. Consulted for the root-level `skills/<name>/SKILL.md` repository convention.
- `vercel-labs/skills` — https://github.com/vercel-labs/skills — revision `5527c09adc367612b0bffd9c80e3bc28a6b01b6d`. Consulted for cross-agent discovery, canonical-copy installation, copy-mode fallback, and Claude Code / Codex agent identifiers.

## Research references

- Wataru Zaitsu and Mingzhe Jin, “Distinguishing ChatGPT(-3.5, -4)-generated and human-written papers through Japanese stylometric analysis,” 2023. https://arxiv.org/abs/2304.05534
- Sora Tarumoto and Hikaru Hatagaki, “Evaluating ChatGPT’s Ability to Generate Japanese,” Journal of Natural Language Processing 31(2), 2024. https://www.jstage.jst.go.jp/article/jnlp/31/2/31_349/_article/-char/en

These works inform feature selection only. This project does not claim to reproduce their experiments or provide reliable authorship detection.
