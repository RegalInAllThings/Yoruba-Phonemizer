"""Compare the neural Yoruba phonemizer with the rule-based engine.

Run from the repository root after installing the project dependencies
and yoruba-g2p==0.2.4.

This is a diagnostic comparison, NOT a gold-accuracy evaluation.
"""

import hashlib
import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yoruba_g2p import YorubaG2P
from yorubag2p_prototype.neural import NeuralConverter
from yorubag2p_prototype.orthography import nasalize_from_spelling


CHECKPOINT = ROOT / "models" / "g2p_silver_model.pt"

EXPECTED_SHA256 = (
    "d4d5d8cc49500946abc1b8f84df7a36bc4df8f5b09849d40db487211b32df217"
)

WORDS = [
    "ẹran",
    "ọrùn",
    "ọ̀run",
    "iyán",
    "ǹkan",
    "gbogbo",
    "àlàáfíà",
    "Yorùbá",
    "ilé",
    "ọmọ",
    "àwọn",
    "ń",
    "ǹ",
]


def main():
    if not CHECKPOINT.exists():
        raise SystemExit(
            f"Checkpoint not found: {CHECKPOINT}"
        )

    digest = hashlib.sha256(CHECKPOINT.read_bytes()).hexdigest()

    if digest != EXPECTED_SHA256:
        raise SystemExit(
            f"Checkpoint hash mismatch: {digest}"
        )

    rule = YorubaG2P()
    neural = NeuralConverter(CHECKPOINT)

    rows = []

    for original in WORDS:
        word = unicodedata.normalize(
            "NFC", original.lower()
        )

        row = {"word": original}

        # Rule-based engine
        try:
            phones, _ = rule.yoruba_word_to_ipa_phones(word)
            row["rule_based"] = list(phones)
        except Exception as exc:
            row["rule_based_error"] = (
                f"{type(exc).__name__}: {exc}"
            )

        # Neural engine
        try:
            raw = neural.word(word)

            row["neural_raw"] = raw

            row["neural_postprocessed"] = (
                nasalize_from_spelling(word, raw)
            )

        except Exception as exc:
            row["neural_error"] = (
                f"{type(exc).__name__}: {exc}"
            )

        rows.append(row)

    report = {
        "note": (
            "Side-by-side diagnostic only. "
            "Neither engine is assumed correct without "
            "expert review."
        ),
        "checkpoint_sha256": digest,
        "words": rows,
    }

    output_path = ROOT / "reports" / "engine_comparison.json"
    output_path.parent.mkdir(
        parents=True, exist_ok=True
    )

    output_path.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print(json.dumps(
        report,
        ensure_ascii=False,
        indent=2
    ))

    print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    main()
