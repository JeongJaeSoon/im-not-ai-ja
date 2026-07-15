# Notices and attribution

## Primary source

This project is an independent Japanese adaptation inspired by and derived in structure from:

- `epoko77-ai/im-not-ai` — https://github.com/epoko77-ai/im-not-ai
- Upstream revision inspected during initial implementation: `14aeb52d13e737beb4e999cb7cb92275d0969689`
- License: MIT
- Copyright: `Copyright (c) 2026 epoko77-ai`

The Fast / Strict workflow, detector–rewriter–auditor separation, severity-based taxonomy, install layout, and content-fidelity contract originate from or are adapted from that project. This repository is not a GitHub fork. The upstream copyright notice and MIT License are preserved in `LICENSE`.

## Japanese open-source references

The Japanese taxonomy was designed after comparing these projects:

- `gonta223/humanizer-ja` — https://github.com/gonta223/humanizer-ja — revision `a1e343696e43aa50e7218891f3319ab22cde3464` — MIT, Copyright (c) 2025 Siqi Chen and Copyright (c) 2026 SuguruKun_ai. Consulted for explicit-subject and uniform-style observations.
- `iKora128/stop-ai-slop-jp` — https://github.com/iKora128/stop-ai-slop-jp — revision `e09d32796f253a62693885757cea484c275d06f2` — MIT, Copyright (c) 2026 Daichi Nagashima. Consulted for false agency, authorial stance, and structure-first editing.
- `makotofalcon/humanizer-ja` — https://github.com/makotofalcon/humanizer-ja — revision `4cc01cdd5aff4102888e9396c3ba16da99828f78` — MIT, Copyright (c) 2025. Consulted for kanji-compound chains and translation-like katakana usage.
- `yourbright-jp/humanizer-jp` — https://github.com/yourbright-jp/humanizer-jp — revision `e252b87c39270a0b9359c1e1e1f8d48b710ff4de` — MIT, Copyright (c) 2026 yourbright-jp. Consulted for sentence-length CV, punctuation, and register-confound findings.

No corpus data from these repositories is redistributed here. Rules were reconciled and rewritten for this project; empirical findings take precedence where heuristic projects disagree.

## Research references

- Wataru Zaitsu and Mingzhe Jin, “Distinguishing ChatGPT(-3.5, -4)-generated and human-written papers through Japanese stylometric analysis,” 2023. https://arxiv.org/abs/2304.05534
- Sora Tarumoto and Hikaru Hatagaki, “Evaluating ChatGPT’s Ability to Generate Japanese,” Journal of Natural Language Processing 31(2), 2024. https://www.jstage.jst.go.jp/article/jnlp/31/2/31_349/_article/-char/en

These works inform feature selection only. This project does not claim to reproduce their experiments or provide reliable authorship detection.
