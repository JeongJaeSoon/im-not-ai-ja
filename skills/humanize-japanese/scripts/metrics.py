#!/usr/bin/env python3
"""Lightweight diagnostics for Japanese AI-writing patterns.

The output is an editing aid, not an authorship classifier.  It deliberately
keeps register metrics descriptive: polite language is not treated as an AI
tell without a context mismatch.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable


VERSION = "0.3.0"

DEFAULT_THRESHOLDS: dict[str, float | int] = {
    "min_sentences": 5,
    "uniform_sentence_cv_warning": 0.60,
    "comma_sentence_ratio_warning": 0.85,
    "top_ending_share_warning": 0.65,
    "connector_sentence_ratio_warning": 0.40,
}

CONNECTORS = (
    "また",
    "さらに",
    "加えて",
    "一方で",
    "しかし",
    "しかしながら",
    "そのため",
    "その結果",
    "したがって",
    "つまり",
    "なお",
)

ENDING_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "business",
        re.compile(
            r"(?:でございます|いたします|申し上げます|存じます|くださいませ|"
            r"させていただきます|させて頂きます)$"
        ),
    ),
    (
        "polite",
        re.compile(
            r"(?:ではありませんでした|ませんでした|でしょう|でした|ません|"
            r"です|ます|ください|願います)$"
        ),
    ),
    (
        "casual",
        re.compile(
            r"(?:じゃない|じゃん|だよね|だよ|だね|よね|かも|かな|してる|よ|ね)$"
        ),
    ),
    (
        "plain",
        re.compile(
            r"(?:ではなかった|である|だろう|だった|ではない|している|しない|"
            r"した|する|ない|ある|なる|だ)$"
        ),
    ),
)

SIGNATURE_PATTERNS: dict[str, re.Pattern[str]] = {
    "A-1": re.compile(
        r"(?:^|[。！？!?]\s*)(?:私は|私たちは|我々は|本稿(?:は|では)|本記事(?:は|では))"
    ),
    "A-7": re.compile(r"することができ(?:ます|る)"),
    "B-1": re.compile(r"することで"),
    "B-2": re.compile(r"だけでなく.{0,40}?も"),
    "B-3": re.compile(
        r"(?:効率化|標準化|自動化|最適化|管理|運用|ツール|機能|製品|サービス|手段|作業)"
        r"(?:から|を超えて)[^。！？!?\n]{0,24}?"
        r"(?:価値|価値創造|体験|パートナー|戦略|未来|変革|成果)(?:へ|に)"
    ),
    "C-1": re.compile(r"包括的|多角的|効果的|革新的|持続可能|シームレス"),
    "C-2": re.compile(r"極めて重要|非常に重要|不可欠|画期的|大きな一歩"),
    "C-3": re.compile(r"(?:推進|促進|醸成|構築|実現)(?:を|の|し|する|して){0,2}"),
    "C-4": re.compile(r"アラインメント|エンパワーメント|ランドスケープ|エコシステム"),
    "C-6": re.compile(r"専門家によれば|多くの研究(?:が|では)|一般に知られて"),
    "D-2": re.compile(r"これにより"),
    "D-3": re.compile(r"そのため|その結果|したがって"),
    "D-4": re.compile(r"(?:^|[。！？!?]\s*)(?:これは|それは|このことは)"),
    "E-3": re.compile(r"と言えるでしょう|といえるでしょう"),
    "E-4": re.compile(r"可能性があるかもしれ|かもしれないと考えられ"),
    "E-5": re.compile(r"することが重要(?:です|である)"),
    "E-6": re.compile(r"期待され(?:ます|る)|注目され(?:ます|る)"),
    "F-1": re.compile(r"(?:三つ|3つ)の(?:観点|ポイント|理由|方法)"),
    "F-6": re.compile(r"課題は残るものの|今後の(?:発展|展開|動向)"),
    "H-1": re.compile(r"\*\*[^*\n]+\*\*"),
    "H-3": re.compile(r"[✅🚀💡✨📌🎯🔥⭐]"),
    "H-4": re.compile(r"――|——|—"),
    "I-1": re.compile(r"浮き彫りに(?:する|した|して|なった|なり)"),
    "I-2": re.compile(r"新たな可能性を切り拓|新しい可能性を切り開"),
    "I-3": re.compile(r"大きな(?:示唆|意義)を(?:持つ|有する)|示唆に富む"),
    "I-4": re.compile(r"単なる.{1,30}?ではなく"),
    "I-5": re.compile(r"一助となれば幸い|今後も注目(?:して|され)"),
}

HONORIFIC_PATTERNS: dict[str, re.Pattern[str]] = {
    "sasete_itadaku": re.compile(r"させて(?:いただ|頂)(?:き|く|け|いた)"),
    "go_ryosho": re.compile(r"ご了承(?:ください|願います|のほど)"),
    "business_polite": re.compile(
        r"いたします|申し上げます|存じます|ございます|伺います|拝見(?:します|いたします)"
    ),
    "double_honorific_candidate": re.compile(
        r"お(?:いで|読み|使い|帰り)になられ|ご利用され|申し上げさせていただ"
    ),
}

PROTECTED_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"https?://[^\s)]+"),
    re.compile(r"`[^`]+`"),
    re.compile(r"[「『\"]([^」』\"]+)[」』\"]"),
    re.compile(r"\d+(?:[.,]\d+)*(?:%|％|円|年|月|日|時|分|秒|件|人|個|倍|GB|MB|kg|km)?"),
)

MODALITY_PATTERNS: dict[str, re.Pattern[str]] = {
    "negation": re.compile(
        r"(?:ない|なかった|ません|ませんでした|できない|不可|禁止|未(?:実施|対応|完了))"
    ),
    "possibility": re.compile(
        r"(?:かもしれ|可能性|おそれ|恐れ|場合があり|場合があります|見込み|得る|うる|でしょう|だろう)"
    ),
    "obligation": re.compile(
        r"(?:なければならない|なくてはならない|必要がある|必要です|べき|義務|必須)"
    ),
    "condition": re.compile(
        r"(?:場合|とき|際|条件|限り|ならば|であれば|のであれば|とすれば|れば[、,]|たら[、,]|なら[、,])"
    ),
}

QUOTED_CONTENT_PATTERN = re.compile(r"「[^「」]*」|『[^『』]*』|\"[^\"\n]*\"")


@dataclass(frozen=True)
class MatchSpan:
    text: str
    start: int
    end: int


@dataclass(frozen=True)
class Finding:
    id: str
    severity: str
    scope: str
    count: int
    reason: str
    note: str = ""
    matches: tuple[MatchSpan, ...] = ()


def strip_nonprose(text: str) -> str:
    """Remove code blocks and URLs while keeping surrounding prose."""
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"^\s*\|.*\|\s*$", " ", text, flags=re.MULTILINE)
    return text


def strip_quoted_content(text: str) -> tuple[str, int]:
    """Exclude quoted voices from document-level register metrics."""
    matches = list(QUOTED_CONTENT_PATTERN.finditer(text))
    return QUOTED_CONTENT_PATTERN.sub(" ", text), len(matches)


def mask_do_not_spans(text: str) -> str:
    """Mask protected/non-prose spans while preserving original offsets."""

    def spaces(match: re.Match[str]) -> str:
        return " " * len(match.group(0))

    masked = re.sub(r"```.*?```", spaces, text, flags=re.DOTALL)
    masked = re.sub(r"`[^`]*`", spaces, masked)
    masked = re.sub(r"https?://\S+", spaces, masked)
    masked = QUOTED_CONTENT_PATTERN.sub(spaces, masked)
    masked = re.sub(r"^\s*\|.*\|\s*$", spaces, masked, flags=re.MULTILINE)
    return masked


def match_spans(pattern: re.Pattern[str], text: str) -> tuple[MatchSpan, ...]:
    return tuple(
        MatchSpan(text=match.group(0), start=match.start(), end=match.end())
        for match in pattern.finditer(text)
    )


def split_sentences(text: str) -> list[str]:
    """Split Japanese prose without a morphological dependency."""
    prose = strip_nonprose(text)
    matches = re.findall(r"[^。！？!?]+[。！？!?]+[」』】）)]*|[^。！？!?]+$", prose)
    sentences: list[str] = []
    for raw in matches:
        sentence = re.sub(r"^\s*(?:[-*+] |\d+[.)] |#{1,6} )", "", raw).strip()
        if sentence and re.search(r"[ぁ-んァ-ヶ一-龯々]", sentence):
            sentences.append(sentence)
    return sentences


def visible_length(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def safe_ratio(numerator: float, denominator: float) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def coefficient_of_variation(values: Iterable[int]) -> float:
    items = list(values)
    if len(items) < 2:
        return 0.0
    mean = statistics.mean(items)
    return round(statistics.pstdev(items) / mean, 4) if mean else 0.0


def classify_ending(sentence: str) -> tuple[str, str]:
    tail = re.sub(r"[。！？!?」』】）)\s]+$", "", sentence)
    for label, pattern in ENDING_PATTERNS:
        match = pattern.search(tail)
        if match:
            return label, match.group(0)
    fallback = tail[-4:] if tail else ""
    return "other", fallback


def script_ratios(text: str) -> dict[str, float]:
    prose = strip_nonprose(text)
    visible = [char for char in prose if not char.isspace()]
    denominator = len(visible)
    hiragana = sum(bool(re.match(r"[ぁ-んゝゞ]", char)) for char in visible)
    katakana = sum(bool(re.match(r"[ァ-ヶー・]", char)) for char in visible)
    kanji = sum(bool(re.match(r"[一-龯々〆ヶ]", char)) for char in visible)
    return {
        "hiragana_ratio": safe_ratio(hiragana, denominator),
        "katakana_ratio": safe_ratio(katakana, denominator),
        "kanji_ratio": safe_ratio(kanji, denominator),
    }


def pattern_counts(text: str) -> dict[str, int]:
    return {pattern_id: len(pattern.findall(text)) for pattern_id, pattern in SIGNATURE_PATTERNS.items()}


def honorific_counts(text: str) -> dict[str, int]:
    return {name: len(pattern.findall(text)) for name, pattern in HONORIFIC_PATTERNS.items()}


def load_thresholds(path: str | Path | None = None) -> dict[str, float | int]:
    thresholds = dict(DEFAULT_THRESHOLDS)
    baseline_path = (
        Path(path)
        if path
        else Path(__file__).resolve().parents[1] / "assets" / "baseline.json"
    )
    if baseline_path.exists():
        data = json.loads(baseline_path.read_text(encoding="utf-8"))
        for key in thresholds:
            if key in data:
                thresholds[key] = data[key]
    return thresholds


def analyze_text(text: str, baseline: str | Path | None = None) -> dict[str, Any]:
    thresholds = load_thresholds(baseline)
    prose = strip_nonprose(text)
    sentences = split_sentences(prose)
    lengths = [visible_length(sentence) for sentence in sentences]
    char_count = visible_length(prose)
    comma_counts = [sentence.count("、") for sentence in sentences]
    comma_sentence_ratio = safe_ratio(sum(count > 0 for count in comma_counts), len(sentences))
    connector_count = sum(
        sentence.lstrip().startswith(CONNECTORS) for sentence in sentences
    )
    connector_ratio = safe_ratio(connector_count, len(sentences))

    register_prose, quoted_segments_excluded = strip_quoted_content(prose)
    register_sentences = split_sentences(register_prose)
    ending_pairs = [classify_ending(sentence) for sentence in register_sentences]
    ending_type_counts = Counter(label for label, _ in ending_pairs)
    ending_surface_counts = Counter(surface for _, surface in ending_pairs if surface)
    classified_count = sum(count for label, count in ending_type_counts.items() if label != "other")
    dominant_register = "unknown"
    if classified_count:
        dominant_register = max(
            (item for item in ending_type_counts.items() if item[0] != "other"),
            key=lambda item: item[1],
        )[0]
    register_mix_ratio = (
        round(1 - max((count for label, count in ending_type_counts.items() if label != "other"), default=0) / classified_count, 4)
        if classified_count
        else 0.0
    )
    top_ending_share = safe_ratio(max(ending_surface_counts.values(), default=0), len(sentences))

    finding_text = mask_do_not_spans(text)
    patterns = pattern_counts(finding_text)
    honorifics = honorific_counts(finding_text)
    findings: list[Finding] = []
    minimum = int(thresholds["min_sentences"])
    cv = coefficient_of_variation(lengths)

    if len(sentences) >= minimum and cv < float(thresholds["uniform_sentence_cv_warning"]):
        findings.append(
            Finding(
                "G-1",
                "S2",
                "document",
                1,
                f"文長CV {cv:.3f} が診断閾値を下回る",
                "ジャンルとレジスターを合わせた比較なしに著者性を断定しない",
            )
        )
    if len(sentences) >= minimum and comma_sentence_ratio >= float(thresholds["comma_sentence_ratio_warning"]):
        findings.append(
            Finding(
                "G-3",
                "S2",
                "document",
                1,
                f"読点を含む文の比率が {comma_sentence_ratio:.1%}",
                "やさしい日本語・仕様書・長文構文では保護する",
            )
        )
    if len(sentences) >= minimum and top_ending_share >= float(thresholds["top_ending_share_warning"]):
        findings.append(
            Finding(
                "E-1",
                "S2",
                "document",
                max(ending_surface_counts.values(), default=0),
                f"最多文末の占有率が {top_ending_share:.1%}",
                "丁寧体そのものではなく同一文末の反復を確認する",
            )
        )
    if len(sentences) >= minimum and connector_ratio >= float(thresholds["connector_sentence_ratio_warning"]):
        findings.append(
            Finding(
                "D-1",
                "S1",
                "document",
                connector_count,
                f"文頭接続詞が {connector_ratio:.1%} の文に出現",
            )
        )

    strong_ids = {"C-1", "C-2", "D-2", "E-5", "E-6", "F-6", "I-1", "I-2", "I-3", "I-5"}
    for pattern_id, pattern in SIGNATURE_PATTERNS.items():
        spans = match_spans(pattern, finding_text)
        count = len(spans)
        if not spans:
            continue
        severity = "S1" if pattern_id in strong_ids and count >= 2 else "S2"
        findings.append(
            Finding(
                pattern_id,
                severity,
                "span",
                count,
                f"{pattern_id} の候補を {count} 件検出",
                "一回の一致だけなら文脈確認を優先する",
                spans,
            )
        )

    if honorifics["double_honorific_candidate"]:
        spans = match_spans(HONORIFIC_PATTERNS["double_honorific_candidate"], finding_text)
        findings.append(
            Finding(
                "E-9",
                "S1",
                "span",
                honorifics["double_honorific_candidate"],
                "尊敬語・謙譲語の重なり候補",
                "行為者と向かう先を確認する",
                spans,
            )
        )
    if honorifics["sasete_itadaku"]:
        spans = match_spans(HONORIFIC_PATTERNS["sasete_itadaku"], finding_text)
        findings.append(
            Finding(
                "E-7",
                "S2",
                "span",
                honorifics["sasete_itadaku"],
                "「させていただく」の場面適合性を要確認",
                "許可と受益があれば保持する。出現自体はAI tellではない",
                spans,
            )
        )
    if honorifics["go_ryosho"]:
        spans = match_spans(HONORIFIC_PATTERNS["go_ryosho"], finding_text)
        findings.append(
            Finding(
                "E-8",
                "S2",
                "span",
                honorifics["go_ryosho"],
                "「ご了承ください」が読み手との距離に合うか要確認",
                "制約受容の正式通知なら保持する",
                spans,
            )
        )

    warnings: list[str] = []
    if len(sentences) < minimum:
        warnings.append(f"短い標本: {len(sentences)}文。計量文体の閾値は適用しない")

    return {
        "version": VERSION,
        "disclaimer": "Editing diagnostics only; not an authorship classifier or detector-bypass score.",
        "warnings": warnings,
        "counts": {
            "characters": char_count,
            "sentences": len(sentences),
            "paragraphs": len([part for part in re.split(r"\n\s*\n", prose) if part.strip()]),
        },
        "rhythm": {
            "sentence_lengths": lengths,
            "sentence_length_mean": round(statistics.mean(lengths), 3) if lengths else 0.0,
            "sentence_length_stdev": round(statistics.pstdev(lengths), 3) if len(lengths) > 1 else 0.0,
            "sentence_length_cv": cv,
            "commas_per_100_chars": round(sum(comma_counts) / char_count * 100, 3) if char_count else 0.0,
            "comma_sentence_ratio": comma_sentence_ratio,
            "connector_sentence_ratio": connector_ratio,
            "top_ending_share": top_ending_share,
        },
        "scripts": script_ratios(prose),
        "register": {
            "dominant": dominant_register,
            "ending_type_counts": dict(ending_type_counts),
            "top_endings": ending_surface_counts.most_common(8),
            "mix_ratio_descriptive_only": register_mix_ratio,
            "honorific_counts": honorifics,
            "quoted_segments_excluded": quoted_segments_excluded,
            "note": "Polite density and mixing are descriptive, not AI tells.",
        },
        "pattern_counts": patterns,
        "findings": [asdict(finding) for finding in findings],
    }


def protected_tokens(text: str) -> Counter[str]:
    tokens: list[str] = []
    for pattern in PROTECTED_PATTERNS:
        for match in pattern.finditer(text):
            tokens.append(match.group(0))
    return Counter(tokens)


def explicit_protected_tokens(text: str, protected: Iterable[str]) -> Counter[str]:
    tokens: Counter[str] = Counter()
    for token in protected:
        if token:
            if re.search(r"[A-Za-z0-9]", token):
                pattern = re.compile(
                    rf"(?<![A-Za-z0-9_.-]){re.escape(token)}(?![A-Za-z0-9_.-])"
                )
                tokens[token] = len(pattern.findall(text))
            else:
                tokens[token] = text.count(token)
    return tokens


def modality_categories(text: str) -> set[str]:
    categories: set[str] = set()
    for name, pattern in MODALITY_PATTERNS.items():
        target = text
        if name == "negation":
            target = re.sub(r"かもしれ(?:ません|ない)", "かもしれ", target)
        if pattern.search(target):
            categories.add(name)
    return categories


def compare_texts(
    before: str,
    after: str,
    protected: Iterable[str] = (),
) -> dict[str, Any]:
    before_tokens = protected_tokens(before)
    after_tokens = protected_tokens(after)
    removed = list((before_tokens - after_tokens).elements())
    added = list((after_tokens - before_tokens).elements())
    explicit_before = explicit_protected_tokens(before, protected)
    explicit_after = explicit_protected_tokens(after, protected)
    explicit_removed = list((explicit_before - explicit_after).elements())
    explicit_added = list((explicit_after - explicit_before).elements())
    modality_before = modality_categories(before)
    modality_after = modality_categories(after)
    modality_removed = sorted(modality_before - modality_after)
    modality_added = sorted(modality_after - modality_before)
    protected_integrity = not removed and not added and not explicit_removed and not explicit_added
    modality_integrity = not modality_removed and not modality_added
    short_sample = visible_length(before) < 100 or len(split_sentences(before)) < 5
    return {
        "change_rate": round(1 - SequenceMatcher(None, before, after).ratio(), 4),
        "characters_before": visible_length(before),
        "characters_after": visible_length(after),
        "short_sample": short_sample,
        "change_rate_policy": (
            "reference_only_for_short_sample" if short_sample else "warn_over_0.30_stop_over_0.50"
        ),
        "protected_removed": removed,
        "protected_added": added,
        "explicit_protected_removed": explicit_removed,
        "explicit_protected_added": explicit_added,
        "protected_integrity": protected_integrity,
        "modality_before": sorted(modality_before),
        "modality_after": sorted(modality_after),
        "modality_removed": modality_removed,
        "modality_added": modality_added,
        "modality_integrity": modality_integrity,
        "contract_integrity": protected_integrity and modality_integrity,
    }


def read_text(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="UTF-8 text/Markdown path, or - for stdin")
    parser.add_argument("--compare", metavar="AFTER", help="Compare protected tokens and change rate")
    parser.add_argument(
        "--protect",
        action="append",
        default=[],
        metavar="TEXT",
        help="Exact protected term; repeat for names and product identifiers",
    )
    parser.add_argument("--baseline", help="Optional baseline JSON")
    parser.add_argument("--compact", action="store_true", help="Print compact JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    before = read_text(args.path)
    output: dict[str, Any] = {"analysis": analyze_text(before, args.baseline)}
    if args.compare:
        after = read_text(args.compare)
        output["after_analysis"] = analyze_text(after, args.baseline)
        output["comparison"] = compare_texts(before, after, args.protect)
    json.dump(output, sys.stdout, ensure_ascii=False, indent=None if args.compact else 2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
