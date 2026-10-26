# YorùbáG2P

Experimental tone-aware Yorùbá grapheme-to-phoneme project.

## Project structure

- src/yorubag2p_prototype/: recovered Stage 7 source code
- models/: recovered Stage 7 neural checkpoint
- data/phase2/: nasalization experiments and diagnostics
- data/gold/: reserved for independently verified references
- notebooks/: recovered Kaggle notebook
- tests/: future regression tests
- scripts/: future training and evaluation scripts
- reports/: project reports and evaluation results

## Important research notes

Stage 7 model metrics were measured against automatically
generated silver labels, not independent gold references.

Phase 2 nasalization modifications remain experimental.

Stage 19L expert linguistic validation is pending.

This development workspace does not yet establish
fully reproducible training. The original training data,
dependencies, random seeds and training configuration
still need to be audited.

Do not replace the original Stage 7 model without
independent evaluation.
