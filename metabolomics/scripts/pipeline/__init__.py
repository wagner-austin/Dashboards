"""
Metabolomics data processing pipeline.

Pipeline stages (in order):
1. load      - Load raw data from Excel
2. blank     - Remove contamination peaks (sample/blank ratio test)
3. cumulative - Keep peaks contributing to top N% of signal
4. diversity - Calculate chemical richness and Shannon diversity
5. overlap   - Calculate treatment overlap (Venn diagram data)
6. render    - Generate HTML dashboard

Each stage reads from the previous stage's output and writes to its own output.
This allows validation at each step and easy insertion of new stages.

Import stage functions directly:
    from scripts.pipeline.loader import load_data
    from scripts.pipeline.blank_filter import filter_blanks
    from scripts.pipeline.cumulative_filter import filter_cumulative
    from scripts.pipeline.diversity import calculate_diversity
    from scripts.pipeline.overlap import calculate_overlap
"""

from scripts.pipeline.types import PipelineState, StageResult

__all__ = [
    "PipelineState",
    "StageResult",
]
