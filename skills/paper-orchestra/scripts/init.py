#!/usr/bin/env python3
"""
init.py - Scaffold the PaperOrchestra desk directory structure.

Usage:
    python scripts/init.py --out desk/
    python scripts/init.py --out my-paper/desk/ --with-examples
"""

import argparse
import os
from pathlib import Path

DESK_STRUCTURE = {
    "inputs": {
        "idea.md": "# Idea Summary\n\n<!-- Write your methodology, core contributions, and theoretical foundation here -->\n\n## Problem Statement\n\n\n## Core Hypothesis\n\n\n## Proposed Methodology\n\n\n## Expected Contribution\n\n",
        "log.md": "# Experimental Log\n\n<!-- Document your experimental setup, raw data, and qualitative observations here -->\n\n## 1. Experimental Setup\n\n### Datasets\n\n\n### Evaluation Metrics\n\n\n### Baselines Compared\n\n\n### Implementation Details\n\n\n## 2. Raw Numeric Data\n\n<!-- Include tables with exact values -->\n\n\n## 3. Qualitative Observations\n\n",
        "tmpl.md": "% LaTeX Template\n% Replace this with your conference's official template\n\n\\documentclass{article}\n\n\\begin{document}\n\n\\title{Your Paper Title}\n\n\\maketitle\n\n\\begin{abstract}\n\\end{abstract}\n\n\\section{Introduction}\n\n\\section{Related Work}\n\n\\section{Method}\n\n\\section{Experiments}\n\n\\section{Conclusion}\n\n\\end{document}\n",
        "gl.md": "# Conference Guidelines\n\n<!-- Specify formatting rules and requirements -->\n\n## Page Limit\n\n\n## Formatting Requirements\n\n\n## Mandatory Sections\n\n\n## Submission Requirements\n\n",
        "fig": None,  # Directory
        "ref": None,  # Directory
    },
    "fig": None,  # Directory for generated figures
    "drafts": None,  # Directory for draft outputs
    "refin": None,  # Directory for refinement iterations
    "final": None,  # Directory for final output
}


EXAMPLE_IDEA = """# Idea Summary

## Problem Statement

The Segment Anything Model (SAM) has established a new baseline for static image segmentation; however, it is structurally ill-equipped for Referring Audio-Visual Segmentation (Ref-AVS). Current foundation models like SAM suffer from two critical limitations:

1. **Lack of Temporal Awareness:** SAM processes inputs as isolated static frames, failing to capture the temporal consistency and dynamic context necessary for video segmentation.
2. **Reliance on Explicit Interaction:** SAM depends on manual user prompts (points, boxes, or masks) to identify targets.

## Core Hypothesis

We hypothesize that we can adapt the frozen, pre-trained knowledge of SAM for dynamic audio-visual scenes without heavy retraining by introducing:
1. A parallel **temporal modeling branch** to inject time-series context
2. **Data-driven multimodal prompts** to replace manual user-in-the-loop prompting

## Proposed Methodology

We propose **TSAM**, a modified architecture that wraps the standard SAM backbone with minimal trainable additions while keeping the heavy image encoder frozen.

### 1. Temporal Modeling Branch
- Sequential processing with cached memory
- Adapter module fusing historical visual states with audio-text embeddings

### 2. Automated Multimodal Prompting
- Sparse Prompting Module (simulating points)
- Dense Prompting Module (simulating masks)

## Expected Contribution

- Architectural novelty: Framework for extending static foundation models to temporal/multimodal domains
- Methodological advancement: "Latent prompting" translating semantic cues to geometric prompts
"""

EXAMPLE_LOG = """# Experimental Log

## 1. Experimental Setup

### Datasets
- **Ref-AVS Dataset:** 20,000 text expressions, 4,000 10-second videos
- **Object Categories:** 20 musical instruments, 8 animals, 15 machines, 5 humans, 3 static inaudible objects
- **Splits:**
  - Training: 2,908 videos
  - Validation: 276 videos
  - Test: 818 videos (Seen: 292, Unseen: 269, Null: 257)

### Evaluation Metrics
- Jaccard Index (J) and F-score (F) for Seen/Unseen
- S metric for Null subset (lower is better)

### Baselines Compared
- AVSBench, AVSegFormer, GAVS, SAMA (AVS methods)
- ReferFormer, R2-VOS (Ref-VOS methods)
- EEMC (previous SOTA)

### Implementation Details
- Model: ViT-B variant of SAM (N=12, d_emb=256)
- Temporal branch: M=4 blocks, k=5 audio queries
- Hardware: 8 AMD GPUs
- Optimizer: AdamW, lr=1e-4, batch_size=1
- Training: 15 epochs

## 2. Raw Numeric Data

| Method | Seen J(%) | Seen F | Unseen J(%) | Unseen F | Null S |
|--------|-----------|--------|-------------|----------|--------|
| EEMC | 34.20 | 0.513 | 49.54 | 0.648 | 0.007 |
| **TSAM (Ours)** | **43.43** | **0.568** | **54.58** | **0.664** | 0.017 |

## 3. Qualitative Observations

- TSAM improved over EEMC by 9.23% Jaccard on Seen, 5.04% on Unseen
- Temporal branch removal caused largest degradation (Seen J: 43.43% → 33.05%)
- k=5 audio queries optimal; k=7 overloads decoder
"""


def create_structure(base_path: Path, structure: dict, with_examples: bool = False):
    """Recursively create directory structure with template files."""
    for name, content in structure.items():
        path = base_path / name
        if content is None:
            # It's a directory
            path.mkdir(parents=True, exist_ok=True)
        elif isinstance(content, dict):
            # Nested structure
            path.mkdir(parents=True, exist_ok=True)
            create_structure(path, content, with_examples)
        else:
            # It's a file with content
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                if with_examples and name == "idea.md":
                    path.write_text(EXAMPLE_IDEA)
                elif with_examples and name == "log.md":
                    path.write_text(EXAMPLE_LOG)
                else:
                    path.write_text(content)


def main():
    parser = argparse.ArgumentParser(
        description="Scaffold the PaperOrchestra desk directory structure"
    )
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Output directory path (e.g., desk/ or my-paper/desk/)",
    )
    parser.add_argument(
        "--with-examples",
        action="store_true",
        help="Include example content in idea.md and log.md",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt when output directory exists",
    )
    args = parser.parse_args()

    base_path = Path(args.out)

    if base_path.exists() and any(base_path.iterdir()):
        if args.yes:
            print(f"Warning: {base_path} already exists and is not empty — overwriting.")
        else:
            print(f"Warning: {base_path} already exists and is not empty")
            response = input("Continue anyway? [y/N] ")
            if response.lower() != "y":
                print("Aborted.")
                return

    print(f"Creating desk structure at: {base_path}")
    create_structure(base_path, DESK_STRUCTURE, args.with_examples)

    print("\nCreated directory structure:")
    for root, _dirs, files in os.walk(base_path):
        level = root.replace(str(base_path), "").count(os.sep)
        indent = "  " * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = "  " * (level + 1)
        for file in files:
            print(f"{subindent}{file}")

    print(f"\n✓ Desk scaffolded at {base_path}")
    print("\nNext steps:")
    print(f"  1. Edit {base_path}/inputs/idea.md with your methodology")
    print(f"  2. Edit {base_path}/inputs/log.md with your experimental results")
    print(f"  3. Replace {base_path}/inputs/tmpl.md with your conference template")
    print(f"  4. Edit {base_path}/inputs/gl.md with conference guidelines")
    print(f"  5. Run: python scripts/validate.py --desk {base_path}")


if __name__ == "__main__":
    main()
