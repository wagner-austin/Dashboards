"""Type definitions for the metabolomics pipeline.

This module defines the data structures passed between pipeline stages.
All types are strict TypedDicts with full validation.

Every TypedDict has:
- decode_* function with require_* validation for deserialization
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TypedDict

import polars as pl

# =============================================================================
# VALIDATION HELPERS (require_* pattern)
# =============================================================================


def require_str(value: object, field_name: str) -> str:
    """Validate and return a string value.

    Args:
        value: The value to validate.
        field_name: Name of the field for error messages.

    Returns:
        The validated string.

    Raises:
        TypeError: If value is not a string.
    """
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be str, got {type(value).__name__}")
    return value


def require_int(value: object, field_name: str) -> int:
    """Validate and return an integer value.

    Args:
        value: The value to validate.
        field_name: Name of the field for error messages.

    Returns:
        The validated integer.

    Raises:
        TypeError: If value is not an int.
    """
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{field_name} must be int, got {type(value).__name__}")
    return value


def require_float(value: object, field_name: str) -> float:
    """Validate and return a float value.

    Args:
        value: The value to validate.
        field_name: Name of the field for error messages.

    Returns:
        The validated float.

    Raises:
        TypeError: If value is not a float or int.
    """
    if isinstance(value, bool):
        raise TypeError(f"{field_name} must be float, got bool")
    if isinstance(value, int):
        return float(value)
    if not isinstance(value, float):
        raise TypeError(f"{field_name} must be float, got {type(value).__name__}")
    return value


def require_bool(value: object, field_name: str) -> bool:
    """Validate and return a boolean value.

    Args:
        value: The value to validate.
        field_name: Name of the field for error messages.

    Returns:
        The validated boolean.

    Raises:
        TypeError: If value is not a bool.
    """
    if not isinstance(value, bool):
        raise TypeError(f"{field_name} must be bool, got {type(value).__name__}")
    return value


def require_list_str(value: object, field_name: str) -> list[str]:
    """Validate and return a list of strings.

    Args:
        value: The value to validate.
        field_name: Name of the field for error messages.

    Returns:
        The validated list of strings.

    Raises:
        TypeError: If value is not a list of strings.
    """
    if not isinstance(value, list):
        raise TypeError(f"{field_name} must be list, got {type(value).__name__}")
    result: list[str] = []
    for i, item in enumerate(value):
        if not isinstance(item, str):
            raise TypeError(f"{field_name}[{i}] must be str, got {type(item).__name__}")
        result.append(item)
    return result


def require_list_float(value: object, field_name: str) -> list[float]:
    """Validate and return a list of floats.

    Args:
        value: The value to validate.
        field_name: Name of the field for error messages.

    Returns:
        The validated list of floats.

    Raises:
        TypeError: If value is not a list of floats.
    """
    if not isinstance(value, list):
        raise TypeError(f"{field_name} must be list, got {type(value).__name__}")
    result: list[float] = []
    for i, item in enumerate(value):
        result.append(require_float(item, f"{field_name}[{i}]"))
    return result


def require_dict(value: object, field_name: str) -> dict[str, object]:
    """Validate and return a dict.

    Args:
        value: The value to validate.
        field_name: Name of the field for error messages.

    Returns:
        The validated dict.

    Raises:
        TypeError: If value is not a dict.
    """
    if not isinstance(value, dict):
        raise TypeError(f"{field_name} must be dict, got {type(value).__name__}")
    return value


# =============================================================================
# CONFIG TYPES
# =============================================================================


class InputConfig(TypedDict):
    """Input file configuration."""

    file: str
    sheet: str
    formula_file: str


class OutputConfig(TypedDict):
    """Output file configuration."""

    html: str
    intermediate_dir: str


class TreatmentSamples(TypedDict):
    """Sample columns for a treatment group."""

    drought: list[str]
    ambient: list[str]
    watered: list[str]


class SamplesConfig(TypedDict):
    """Sample configuration by tissue."""

    leaf: TreatmentSamples
    root: TreatmentSamples


class BlanksConfig(TypedDict):
    """Blank column configuration by tissue."""

    leaf: list[str]
    root: list[str]


class BlankFilterThresholds(TypedDict):
    """Thresholds for blank filtering."""

    fold_change: float
    p_value: float
    fdr_correction: bool
    reference: str
    citation: str


class CumulativeFilterThresholds(TypedDict):
    """Thresholds for cumulative filtering."""

    threshold: float
    description: str


class DetectionThresholds(TypedDict):
    """Detection thresholds."""

    min_value: float
    description: str


class ThresholdsConfig(TypedDict):
    """All threshold configurations."""

    blank_filter: BlankFilterThresholds
    cumulative_filter: CumulativeFilterThresholds
    detection: DetectionThresholds


class ReferenceEntry(TypedDict):
    """A single reference citation."""

    name: str
    url: str
    citation: str


class ReferencesConfig(TypedDict):
    """Reference citations."""

    blank_subtraction: ReferenceEntry
    shannon_diversity: ReferenceEntry
    fdr_correction: ReferenceEntry


class Config(TypedDict):
    """Complete pipeline configuration."""

    input: InputConfig
    output: OutputConfig
    samples: SamplesConfig
    blanks: BlanksConfig
    thresholds: ThresholdsConfig
    references: ReferencesConfig


# =============================================================================
# CONFIG DECODE FUNCTIONS
# =============================================================================


def decode_input_config(raw: dict[str, object]) -> InputConfig:
    """Decode and validate InputConfig from raw dict.

    Args:
        raw: Raw dict from JSON.

    Returns:
        Validated InputConfig.

    Raises:
        TypeError: If validation fails.
        KeyError: If required key is missing.
    """
    formula_file_raw = raw.get("formula_file", "")
    return InputConfig(
        file=require_str(raw["file"], "input.file"),
        sheet=require_str(raw["sheet"], "input.sheet"),
        formula_file=require_str(formula_file_raw, "input.formula_file"),
    )


def decode_output_config(raw: dict[str, object]) -> OutputConfig:
    """Decode and validate OutputConfig from raw dict.

    Args:
        raw: Raw dict from JSON.

    Returns:
        Validated OutputConfig.

    Raises:
        TypeError: If validation fails.
        KeyError: If required key is missing.
    """
    intermediate_raw = raw.get("intermediate_dir", "intermediate")
    return OutputConfig(
        html=require_str(raw["html"], "output.html"),
        intermediate_dir=require_str(intermediate_raw, "output.intermediate_dir"),
    )


def decode_treatment_samples(raw: dict[str, object], tissue: str) -> TreatmentSamples:
    """Decode and validate TreatmentSamples from raw dict.

    Args:
        raw: Raw dict from JSON.
        tissue: Tissue name for error messages.

    Returns:
        Validated TreatmentSamples.

    Raises:
        TypeError: If validation fails.
        KeyError: If required key is missing.
    """
    return TreatmentSamples(
        drought=require_list_str(raw["drought"], f"samples.{tissue}.drought"),
        ambient=require_list_str(raw["ambient"], f"samples.{tissue}.ambient"),
        watered=require_list_str(raw["watered"], f"samples.{tissue}.watered"),
    )


def decode_samples_config(raw: dict[str, object]) -> SamplesConfig:
    """Decode and validate SamplesConfig from raw dict.

    Args:
        raw: Raw dict from JSON.

    Returns:
        Validated SamplesConfig.

    Raises:
        TypeError: If validation fails.
        KeyError: If required key is missing.
    """
    leaf_raw = require_dict(raw["leaf"], "samples.leaf")
    root_raw = require_dict(raw["root"], "samples.root")
    return SamplesConfig(
        leaf=decode_treatment_samples(leaf_raw, "leaf"),
        root=decode_treatment_samples(root_raw, "root"),
    )


def decode_blanks_config(raw: dict[str, object]) -> BlanksConfig:
    """Decode and validate BlanksConfig from raw dict.

    Args:
        raw: Raw dict from JSON.

    Returns:
        Validated BlanksConfig.

    Raises:
        TypeError: If validation fails.
        KeyError: If required key is missing.
    """
    return BlanksConfig(
        leaf=require_list_str(raw["leaf"], "blanks.leaf"),
        root=require_list_str(raw["root"], "blanks.root"),
    )


def decode_blank_filter_thresholds(raw: dict[str, object]) -> BlankFilterThresholds:
    """Decode and validate BlankFilterThresholds from raw dict.

    Args:
        raw: Raw dict from JSON.

    Returns:
        Validated BlankFilterThresholds.

    Raises:
        TypeError: If validation fails.
        KeyError: If required key is missing.
    """
    ref_raw = raw.get("reference", "")
    cit_raw = raw.get("citation", "")
    return BlankFilterThresholds(
        fold_change=require_float(raw["fold_change"], "thresholds.blank_filter.fold_change"),
        p_value=require_float(raw["p_value"], "thresholds.blank_filter.p_value"),
        fdr_correction=require_bool(
            raw["fdr_correction"], "thresholds.blank_filter.fdr_correction"
        ),
        reference=require_str(ref_raw, "thresholds.blank_filter.reference"),
        citation=require_str(cit_raw, "thresholds.blank_filter.citation"),
    )


def decode_cumulative_filter_thresholds(raw: dict[str, object]) -> CumulativeFilterThresholds:
    """Decode and validate CumulativeFilterThresholds from raw dict.

    Args:
        raw: Raw dict from JSON.

    Returns:
        Validated CumulativeFilterThresholds.

    Raises:
        TypeError: If validation fails.
        KeyError: If required key is missing.
    """
    desc_raw = raw.get("description", "")
    return CumulativeFilterThresholds(
        threshold=require_float(raw["threshold"], "thresholds.cumulative_filter.threshold"),
        description=require_str(desc_raw, "thresholds.cumulative_filter.description"),
    )


def decode_detection_thresholds(raw: dict[str, object]) -> DetectionThresholds:
    """Decode and validate DetectionThresholds from raw dict.

    Args:
        raw: Raw dict from JSON.

    Returns:
        Validated DetectionThresholds.

    Raises:
        TypeError: If validation fails.
        KeyError: If required key is missing.
    """
    desc_raw = raw.get("description", "")
    return DetectionThresholds(
        min_value=require_float(raw["min_value"], "thresholds.detection.min_value"),
        description=require_str(desc_raw, "thresholds.detection.description"),
    )


def decode_thresholds_config(raw: dict[str, object]) -> ThresholdsConfig:
    """Decode and validate ThresholdsConfig from raw dict.

    Args:
        raw: Raw dict from JSON.

    Returns:
        Validated ThresholdsConfig.

    Raises:
        TypeError: If validation fails.
        KeyError: If required key is missing.
    """
    blank_raw = require_dict(raw["blank_filter"], "thresholds.blank_filter")
    cumulative_raw = require_dict(raw["cumulative_filter"], "thresholds.cumulative_filter")
    detection_raw = require_dict(raw["detection"], "thresholds.detection")
    return ThresholdsConfig(
        blank_filter=decode_blank_filter_thresholds(blank_raw),
        cumulative_filter=decode_cumulative_filter_thresholds(cumulative_raw),
        detection=decode_detection_thresholds(detection_raw),
    )


def decode_reference_entry(raw: dict[str, object], name: str) -> ReferenceEntry:
    """Decode and validate ReferenceEntry from raw dict.

    Args:
        raw: Raw dict from JSON.
        name: Reference name for error messages.

    Returns:
        Validated ReferenceEntry.

    Raises:
        TypeError: If validation fails.
        KeyError: If required key is missing.
    """
    return ReferenceEntry(
        name=require_str(raw["name"], f"references.{name}.name"),
        url=require_str(raw["url"], f"references.{name}.url"),
        citation=require_str(raw["citation"], f"references.{name}.citation"),
    )


def decode_references_config(raw: dict[str, object]) -> ReferencesConfig:
    """Decode and validate ReferencesConfig from raw dict.

    Args:
        raw: Raw dict from JSON.

    Returns:
        Validated ReferencesConfig.

    Raises:
        TypeError: If validation fails.
        KeyError: If required key is missing.
    """
    blank_raw = require_dict(raw["blank_subtraction"], "references.blank_subtraction")
    shannon_raw = require_dict(raw["shannon_diversity"], "references.shannon_diversity")
    fdr_raw = require_dict(raw["fdr_correction"], "references.fdr_correction")
    return ReferencesConfig(
        blank_subtraction=decode_reference_entry(blank_raw, "blank_subtraction"),
        shannon_diversity=decode_reference_entry(shannon_raw, "shannon_diversity"),
        fdr_correction=decode_reference_entry(fdr_raw, "fdr_correction"),
    )


def decode_config(raw: dict[str, object]) -> Config:
    """Decode and validate Config from raw dict.

    Args:
        raw: Raw dict from JSON.

    Returns:
        Validated Config.

    Raises:
        TypeError: If validation fails.
        KeyError: If required key is missing.
    """
    input_raw = require_dict(raw["input"], "input")
    output_raw = require_dict(raw["output"], "output")
    samples_raw = require_dict(raw["samples"], "samples")
    blanks_raw = require_dict(raw["blanks"], "blanks")
    thresholds_raw = require_dict(raw["thresholds"], "thresholds")
    references_raw = require_dict(raw["references"], "references")

    return Config(
        input=decode_input_config(input_raw),
        output=decode_output_config(output_raw),
        samples=decode_samples_config(samples_raw),
        blanks=decode_blanks_config(blanks_raw),
        thresholds=decode_thresholds_config(thresholds_raw),
        references=decode_references_config(references_raw),
    )


# =============================================================================
# FILTER STATS TYPES
# =============================================================================


class BlankFilterStats(TypedDict):
    """Statistics from blank filtering stage."""

    sample_only: int
    both_keep: int
    both_discard: int
    blank_only: int
    neither: int
    fold_change_pass: int
    fold_change_fail: int
    stat_test_pass: int
    stat_test_fail: int
    insufficient_data: int
    total_clean: int
    statistical_test_used: bool
    fdr_corrected: bool
    p_value_cutoff: float
    fold_change_threshold: float


def create_blank_filter_stats(
    *,
    sample_only: int = 0,
    both_keep: int = 0,
    both_discard: int = 0,
    blank_only: int = 0,
    neither: int = 0,
    fold_change_pass: int = 0,
    fold_change_fail: int = 0,
    stat_test_pass: int = 0,
    stat_test_fail: int = 0,
    insufficient_data: int = 0,
    statistical_test_used: bool = True,
    fdr_corrected: bool = True,
    p_value_cutoff: float = 0.05,
    fold_change_threshold: float = 20.0,
) -> BlankFilterStats:
    """Create a BlankFilterStats with computed total_clean.

    Args:
        sample_only: Peaks only in samples (auto-kept).
        both_keep: Peaks in both that passed criteria.
        both_discard: Peaks in both that failed criteria.
        blank_only: Peaks only in blanks.
        neither: Peaks in neither.
        fold_change_pass: Peaks that passed fold-change test.
        fold_change_fail: Peaks that failed fold-change test.
        stat_test_pass: Peaks that passed statistical test.
        stat_test_fail: Peaks that failed statistical test.
        insufficient_data: Peaks with insufficient data for t-test.
        statistical_test_used: Whether t-test was used.
        fdr_corrected: Whether FDR correction was applied.
        p_value_cutoff: P-value threshold used.
        fold_change_threshold: Fold-change threshold used.

    Returns:
        BlankFilterStats with total_clean computed.
    """
    return BlankFilterStats(
        sample_only=sample_only,
        both_keep=both_keep,
        both_discard=both_discard,
        blank_only=blank_only,
        neither=neither,
        fold_change_pass=fold_change_pass,
        fold_change_fail=fold_change_fail,
        stat_test_pass=stat_test_pass,
        stat_test_fail=stat_test_fail,
        insufficient_data=insufficient_data,
        total_clean=sample_only + both_keep,
        statistical_test_used=statistical_test_used,
        fdr_corrected=fdr_corrected,
        p_value_cutoff=p_value_cutoff,
        fold_change_threshold=fold_change_threshold,
    )


# =============================================================================
# DIVERSITY TYPES
# =============================================================================


class DiversityResult(TypedDict):
    """Diversity metrics for a single treatment group."""

    mean: float
    se: float
    n: int
    values: list[float]


def create_diversity_result(values: list[float]) -> DiversityResult:
    """Create a DiversityResult with computed mean and SE.

    Args:
        values: List of diversity values per sample.

    Returns:
        DiversityResult with mean and SE computed.
    """
    if not values:
        return DiversityResult(mean=0.0, se=0.0, n=0, values=[])

    n = len(values)
    mean = sum(values) / n

    if n < 2:
        se = 0.0
    else:
        variance = sum((x - mean) ** 2 for x in values) / (n - 1)
        se = math.sqrt(variance / n)

    return DiversityResult(mean=mean, se=se, n=n, values=list(values))


class TreatmentDiversity(TypedDict):
    """Diversity metrics for all treatments in a tissue."""

    Drought: DiversityResult
    Ambient: DiversityResult
    Watered: DiversityResult


# =============================================================================
# VENN DATA TYPES
# =============================================================================


class VennData(TypedDict):
    """Venn diagram data for a single tissue."""

    drought: int
    ambient: int
    watered: int
    all: int
    drought_only: int
    ambient_only: int
    watered_only: int
    drought_ambient: int
    drought_watered: int
    ambient_watered: int
    all_three: int


# =============================================================================
# PIPELINE STATE
# =============================================================================


@dataclass
class StageResult:
    """Result from a single pipeline stage."""

    stage_name: str
    success: bool
    message: str
    input_count: int = 0
    output_count: int = 0
    data: dict[str, object] | None = None


@dataclass
class PipelineState:
    """State passed between pipeline stages.

    Each stage reads from this state and returns an updated copy.
    This allows validation at each step and clear data lineage.

    DATA FLOW:
        load stage:
            df_raw -> raw data from Excel (23,134 peaks)

        blank_filter stage:
            df_blank_filtered -> after blank subtraction (14,307 peaks)
            kept_blank -> set of compound names that passed
            blank_stats -> detailed statistics

        cumulative_filter stage:
            df_80 -> after 80% cumulative filter (1,626 peaks)
            kept_80 -> set of compound names that passed
            sample_data_80 -> per-sample filtering stats

        diversity stage:
            chemical_richness -> richness per tissue/treatment
            shannon_diversity -> Shannon H per tissue/treatment
            (NOTE: calculated from df_blank_filtered, NOT df_80)

        overlap stage:
            venn_data -> counts for Venn diagrams
            treatment_peaks -> actual peak sets
    """

    # Configuration (immutable after load)
    config: Config | None = None

    # Raw data from Excel
    df_raw: pl.DataFrame | None = None
    formula_lookup: dict[str, str] = field(default_factory=dict)

    # After blank filtering
    df_blank_filtered: pl.DataFrame | None = None
    kept_blank: set[str] = field(default_factory=set)
    blank_stats: BlankFilterStats | None = None

    # After cumulative filtering
    df_80: pl.DataFrame | None = None
    kept_80: set[str] = field(default_factory=set)
    sample_data_80: list[tuple[str, str, int, float]] = field(default_factory=list)

    # Diversity metrics (from df_blank_filtered)
    chemical_richness: dict[str, TreatmentDiversity] = field(default_factory=dict)
    shannon_diversity: dict[str, TreatmentDiversity] = field(default_factory=dict)

    # Overlap data
    venn_data: dict[str, VennData] = field(default_factory=dict)
    treatment_peaks: dict[str, dict[str, set[str]]] = field(default_factory=dict)

    # Stage tracking
    completed_stages: list[str] = field(default_factory=list)
    stage_results: list[StageResult] = field(default_factory=list)

    def add_stage_result(self, result: StageResult) -> None:
        """Record a stage result.

        Args:
            result: The stage result to record.
        """
        self.stage_results.append(result)
        if result.success:
            self.completed_stages.append(result.stage_name)

    def validate(self) -> list[str]:
        """Validate current state, return list of errors.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors: list[str] = []

        if self.config is None:
            errors.append("Config not loaded")

        if "blank_filter" in self.completed_stages:
            if self.df_blank_filtered is None:
                errors.append("blank_filter completed but df_blank_filtered is None")
            if not self.kept_blank:
                errors.append("blank_filter completed but kept_blank is empty")

        if "cumulative_filter" in self.completed_stages:
            if self.df_80 is None:
                errors.append("cumulative_filter completed but df_80 is None")
            if not self.kept_80:
                errors.append("cumulative_filter completed but kept_80 is empty")

        if "diversity" in self.completed_stages:
            if not self.chemical_richness:
                errors.append("diversity completed but chemical_richness is empty")
            if not self.shannon_diversity:
                errors.append("diversity completed but shannon_diversity is empty")

        return errors
