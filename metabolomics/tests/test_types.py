"""Tests for the pipeline types module."""

from __future__ import annotations

import pytest

from scripts.pipeline.types import (
    PipelineState,
    StageResult,
    create_blank_filter_stats,
    create_diversity_result,
    decode_blank_filter_thresholds,
    decode_blanks_config,
    decode_config,
    decode_cumulative_filter_thresholds,
    decode_detection_thresholds,
    decode_input_config,
    decode_output_config,
    decode_reference_entry,
    decode_references_config,
    decode_samples_config,
    decode_thresholds_config,
    decode_treatment_samples,
    require_bool,
    require_dict,
    require_float,
    require_int,
    require_list_float,
    require_list_str,
    require_str,
)


class TestRequireStr:
    """Tests for require_str validation."""

    def test_valid_string(self) -> None:
        """Test valid string passes."""
        assert require_str("hello", "field") == "hello"

    def test_empty_string(self) -> None:
        """Test empty string is valid."""
        assert require_str("", "field") == ""

    def test_non_string_raises(self) -> None:
        """Test non-string raises TypeError."""
        with pytest.raises(TypeError, match="field must be str, got int"):
            require_str(123, "field")


class TestRequireInt:
    """Tests for require_int validation."""

    def test_valid_int(self) -> None:
        """Test valid int passes."""
        assert require_int(42, "field") == 42

    def test_zero(self) -> None:
        """Test zero is valid."""
        assert require_int(0, "field") == 0

    def test_negative(self) -> None:
        """Test negative int is valid."""
        assert require_int(-5, "field") == -5

    def test_bool_raises(self) -> None:
        """Test bool raises TypeError (bool is subclass of int)."""
        with pytest.raises(TypeError, match="field must be int, got bool"):
            require_int(True, "field")

    def test_float_raises(self) -> None:
        """Test float raises TypeError."""
        with pytest.raises(TypeError, match="field must be int, got float"):
            require_int(3.14, "field")


class TestRequireFloat:
    """Tests for require_float validation."""

    def test_valid_float(self) -> None:
        """Test valid float passes."""
        assert require_float(3.14, "field") == 3.14

    def test_int_converted_to_float(self) -> None:
        """Test int is converted to float."""
        result = require_float(42, "field")
        assert result == 42.0
        assert isinstance(result, float)

    def test_zero(self) -> None:
        """Test zero is valid."""
        assert require_float(0.0, "field") == 0.0

    def test_bool_raises(self) -> None:
        """Test bool raises TypeError."""
        with pytest.raises(TypeError, match="field must be float, got bool"):
            require_float(True, "field")

    def test_string_raises(self) -> None:
        """Test string raises TypeError."""
        with pytest.raises(TypeError, match="field must be float, got str"):
            require_float("3.14", "field")


class TestRequireBool:
    """Tests for require_bool validation."""

    def test_true(self) -> None:
        """Test True passes."""
        assert require_bool(True, "field") is True

    def test_false(self) -> None:
        """Test False passes."""
        assert require_bool(False, "field") is False

    def test_int_raises(self) -> None:
        """Test int raises TypeError."""
        with pytest.raises(TypeError, match="field must be bool, got int"):
            require_bool(1, "field")

    def test_string_raises(self) -> None:
        """Test string raises TypeError."""
        with pytest.raises(TypeError, match="field must be bool, got str"):
            require_bool("true", "field")


class TestRequireListStr:
    """Tests for require_list_str validation."""

    def test_valid_list(self) -> None:
        """Test valid list of strings passes."""
        assert require_list_str(["a", "b", "c"], "field") == ["a", "b", "c"]

    def test_empty_list(self) -> None:
        """Test empty list is valid."""
        assert require_list_str([], "field") == []

    def test_not_list_raises(self) -> None:
        """Test non-list raises TypeError."""
        with pytest.raises(TypeError, match="field must be list, got str"):
            require_list_str("not a list", "field")

    def test_list_with_non_string_raises(self) -> None:
        """Test list with non-string element raises TypeError."""
        with pytest.raises(TypeError, match=r"field\[1\] must be str, got int"):
            require_list_str(["a", 123, "c"], "field")


class TestRequireListFloat:
    """Tests for require_list_float validation."""

    def test_valid_list(self) -> None:
        """Test valid list of floats passes."""
        assert require_list_float([1.0, 2.5, 3.0], "field") == [1.0, 2.5, 3.0]

    def test_ints_converted(self) -> None:
        """Test ints in list are converted to floats."""
        result = require_list_float([1, 2, 3], "field")
        assert result == [1.0, 2.0, 3.0]
        assert all(isinstance(v, float) for v in result)

    def test_empty_list(self) -> None:
        """Test empty list is valid."""
        assert require_list_float([], "field") == []

    def test_not_list_raises(self) -> None:
        """Test non-list raises TypeError."""
        with pytest.raises(TypeError, match="field must be list, got tuple"):
            require_list_float((1.0, 2.0), "field")


class TestRequireDict:
    """Tests for require_dict validation."""

    def test_valid_dict(self) -> None:
        """Test valid dict passes."""
        result = require_dict({"a": 1, "b": 2}, "field")
        assert result == {"a": 1, "b": 2}

    def test_empty_dict(self) -> None:
        """Test empty dict is valid."""
        assert require_dict({}, "field") == {}

    def test_not_dict_raises(self) -> None:
        """Test non-dict raises TypeError."""
        with pytest.raises(TypeError, match="field must be dict, got list"):
            require_dict([1, 2, 3], "field")


class TestDecodeInputConfig:
    """Tests for decode_input_config."""

    def test_valid_config(self) -> None:
        """Test valid input config decodes correctly."""
        raw: dict[str, object] = {
            "file": "data.xlsx",
            "sheet": "Sheet1",
            "formula_file": "formulas.xlsx",
        }
        result = decode_input_config(raw)
        assert result["file"] == "data.xlsx"
        assert result["sheet"] == "Sheet1"
        assert result["formula_file"] == "formulas.xlsx"

    def test_missing_formula_file_defaults_empty(self) -> None:
        """Test missing formula_file defaults to empty string."""
        raw: dict[str, object] = {"file": "data.xlsx", "sheet": "Sheet1"}
        result = decode_input_config(raw)
        assert result["formula_file"] == ""

    def test_missing_required_key_raises(self) -> None:
        """Test missing required key raises KeyError."""
        raw: dict[str, object] = {"file": "data.xlsx"}
        with pytest.raises(KeyError):
            decode_input_config(raw)


class TestDecodeOutputConfig:
    """Tests for decode_output_config."""

    def test_valid_config(self) -> None:
        """Test valid output config decodes correctly."""
        raw: dict[str, object] = {"html": "dashboard.html", "intermediate_dir": "output"}
        result = decode_output_config(raw)
        assert result["html"] == "dashboard.html"
        assert result["intermediate_dir"] == "output"

    def test_missing_intermediate_dir_defaults(self) -> None:
        """Test missing intermediate_dir defaults to 'intermediate'."""
        raw: dict[str, object] = {"html": "dashboard.html"}
        result = decode_output_config(raw)
        assert result["intermediate_dir"] == "intermediate"


class TestDecodeTreatmentSamples:
    """Tests for decode_treatment_samples."""

    def test_valid_samples(self) -> None:
        """Test valid treatment samples decode correctly."""
        raw: dict[str, object] = {
            "drought": ["A1", "A2"],
            "ambient": ["B1"],
            "watered": ["C1", "C2", "C3"],
        }
        result = decode_treatment_samples(raw, "leaf")
        assert result["drought"] == ["A1", "A2"]
        assert result["ambient"] == ["B1"]
        assert result["watered"] == ["C1", "C2", "C3"]


class TestDecodeSamplesConfig:
    """Tests for decode_samples_config."""

    def test_valid_config(self) -> None:
        """Test valid samples config decodes correctly."""
        raw: dict[str, object] = {
            "leaf": {"drought": [], "ambient": [], "watered": []},
            "root": {"drought": [], "ambient": [], "watered": []},
        }
        result = decode_samples_config(raw)
        assert "leaf" in result
        assert "root" in result


class TestDecodeBlanksConfig:
    """Tests for decode_blanks_config."""

    def test_valid_config(self) -> None:
        """Test valid blanks config decodes correctly."""
        raw: dict[str, object] = {"leaf": ["Blk1", "Blk2"], "root": ["RBlk1"]}
        result = decode_blanks_config(raw)
        assert result["leaf"] == ["Blk1", "Blk2"]
        assert result["root"] == ["RBlk1"]


class TestDecodeBlankFilterThresholds:
    """Tests for decode_blank_filter_thresholds."""

    def test_valid_thresholds(self) -> None:
        """Test valid thresholds decode correctly."""
        raw: dict[str, object] = {
            "fold_change": 20.0,
            "p_value": 0.05,
            "fdr_correction": True,
        }
        result = decode_blank_filter_thresholds(raw)
        assert result["fold_change"] == 20.0
        assert result["p_value"] == 0.05
        assert result["fdr_correction"] is True

    def test_optional_reference_fields(self) -> None:
        """Test reference fields default to empty string."""
        raw: dict[str, object] = {
            "fold_change": 20.0,
            "p_value": 0.05,
            "fdr_correction": True,
        }
        result = decode_blank_filter_thresholds(raw)
        assert result["reference"] == ""
        assert result["citation"] == ""


class TestDecodeCumulativeFilterThresholds:
    """Tests for decode_cumulative_filter_thresholds."""

    def test_valid_thresholds(self) -> None:
        """Test valid thresholds decode correctly."""
        raw: dict[str, object] = {"threshold": 0.80, "description": "Keep top 80%"}
        result = decode_cumulative_filter_thresholds(raw)
        assert result["threshold"] == 0.80
        assert result["description"] == "Keep top 80%"


class TestDecodeDetectionThresholds:
    """Tests for decode_detection_thresholds."""

    def test_valid_thresholds(self) -> None:
        """Test valid thresholds decode correctly."""
        raw: dict[str, object] = {"min_value": 0.0, "description": "Minimum detection"}
        result = decode_detection_thresholds(raw)
        assert result["min_value"] == 0.0
        assert result["description"] == "Minimum detection"


class TestDecodeThresholdsConfig:
    """Tests for decode_thresholds_config."""

    def test_valid_config(self) -> None:
        """Test valid thresholds config decodes correctly."""
        raw: dict[str, object] = {
            "blank_filter": {"fold_change": 20.0, "p_value": 0.05, "fdr_correction": True},
            "cumulative_filter": {"threshold": 0.80},
            "detection": {"min_value": 0.0},
        }
        result = decode_thresholds_config(raw)
        assert result["blank_filter"]["fold_change"] == 20.0
        assert result["cumulative_filter"]["threshold"] == 0.80
        assert result["detection"]["min_value"] == 0.0


class TestDecodeReferenceEntry:
    """Tests for decode_reference_entry."""

    def test_valid_entry(self) -> None:
        """Test valid reference entry decodes correctly."""
        raw: dict[str, object] = {
            "name": "pmp",
            "url": "https://example.com",
            "citation": "Author 2020",
        }
        result = decode_reference_entry(raw, "blank_subtraction")
        assert result["name"] == "pmp"
        assert result["url"] == "https://example.com"
        assert result["citation"] == "Author 2020"


class TestDecodeReferencesConfig:
    """Tests for decode_references_config."""

    def test_valid_config(self) -> None:
        """Test valid references config decodes correctly."""
        entry: dict[str, object] = {"name": "", "url": "", "citation": ""}
        raw: dict[str, object] = {
            "blank_subtraction": entry,
            "shannon_diversity": entry,
            "fdr_correction": entry,
        }
        result = decode_references_config(raw)
        assert "blank_subtraction" in result
        assert "shannon_diversity" in result
        assert "fdr_correction" in result


class TestDecodeConfig:
    """Tests for decode_config."""

    def test_valid_full_config(self) -> None:
        """Test valid full config decodes correctly."""
        raw: dict[str, object] = {
            "input": {"file": "data.xlsx", "sheet": "Sheet1"},
            "output": {"html": "dashboard.html"},
            "samples": {
                "leaf": {"drought": [], "ambient": [], "watered": []},
                "root": {"drought": [], "ambient": [], "watered": []},
            },
            "blanks": {"leaf": [], "root": []},
            "thresholds": {
                "blank_filter": {"fold_change": 20.0, "p_value": 0.05, "fdr_correction": True},
                "cumulative_filter": {"threshold": 0.80},
                "detection": {"min_value": 0.0},
            },
            "references": {
                "blank_subtraction": {"name": "", "url": "", "citation": ""},
                "shannon_diversity": {"name": "", "url": "", "citation": ""},
                "fdr_correction": {"name": "", "url": "", "citation": ""},
            },
        }
        result = decode_config(raw)
        assert result["input"]["file"] == "data.xlsx"
        assert result["thresholds"]["blank_filter"]["fold_change"] == 20.0


class TestCreateBlankFilterStats:
    """Tests for create_blank_filter_stats."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        result = create_blank_filter_stats()
        assert result["sample_only"] == 0
        assert result["both_keep"] == 0
        assert result["total_clean"] == 0
        assert result["statistical_test_used"] is True
        assert result["fdr_corrected"] is True
        assert result["p_value_cutoff"] == 0.05
        assert result["fold_change_threshold"] == 20.0

    def test_total_clean_computed(self) -> None:
        """Test total_clean is computed from sample_only + both_keep."""
        result = create_blank_filter_stats(sample_only=100, both_keep=50)
        assert result["total_clean"] == 150

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        result = create_blank_filter_stats(
            sample_only=10,
            both_keep=20,
            both_discard=5,
            statistical_test_used=False,
            fold_change_threshold=3.0,
        )
        assert result["sample_only"] == 10
        assert result["both_keep"] == 20
        assert result["both_discard"] == 5
        assert result["statistical_test_used"] is False
        assert result["fold_change_threshold"] == 3.0


class TestCreateDiversityResult:
    """Tests for create_diversity_result."""

    def test_empty_values(self) -> None:
        """Test empty values returns zeros."""
        result = create_diversity_result([])
        assert result["mean"] == 0.0
        assert result["se"] == 0.0
        assert result["n"] == 0
        assert result["values"] == []

    def test_single_value(self) -> None:
        """Test single value returns mean with zero SE."""
        result = create_diversity_result([5.0])
        assert result["mean"] == 5.0
        assert result["se"] == 0.0
        assert result["n"] == 1

    def test_multiple_values(self) -> None:
        """Test multiple values computes mean and SE."""
        result = create_diversity_result([2.0, 4.0, 6.0])
        assert result["mean"] == 4.0
        assert result["n"] == 3
        assert result["se"] > 0  # SE should be positive


class TestPipelineState:
    """Tests for PipelineState dataclass."""

    def test_default_state(self) -> None:
        """Test default state has expected values."""
        state = PipelineState()
        assert state.config is None
        assert state.df_raw is None
        assert state.formula_lookup == {}
        assert state.completed_stages == []
        assert state.stage_results == []

    def test_add_stage_result_success(self) -> None:
        """Test adding successful stage result."""
        state = PipelineState()
        result = StageResult(stage_name="load", success=True, message="Loaded")
        state.add_stage_result(result)

        assert len(state.stage_results) == 1
        assert "load" in state.completed_stages

    def test_add_stage_result_failure(self) -> None:
        """Test adding failed stage result doesn't add to completed."""
        state = PipelineState()
        result = StageResult(stage_name="load", success=False, message="Failed")
        state.add_stage_result(result)

        assert len(state.stage_results) == 1
        assert "load" not in state.completed_stages

    def test_validate_empty_state(self) -> None:
        """Test validating empty state reports config missing."""
        state = PipelineState()
        errors = state.validate()
        assert "Config not loaded" in errors

    def test_validate_blank_filter_completed_but_data_missing(self) -> None:
        """Test validation catches missing data after stage completion."""
        state = PipelineState()
        state.completed_stages.append("blank_filter")
        errors = state.validate()
        assert any("df_blank_filtered is None" in e for e in errors)
        assert any("kept_blank is empty" in e for e in errors)

    def test_validate_cumulative_filter_completed_but_data_missing(self) -> None:
        """Test validation catches missing cumulative filter data."""
        state = PipelineState()
        state.completed_stages.append("cumulative_filter")
        errors = state.validate()
        assert any("df_80 is None" in e for e in errors)
        assert any("kept_80 is empty" in e for e in errors)

    def test_validate_diversity_completed_but_data_missing(self) -> None:
        """Test validation catches missing diversity data."""
        state = PipelineState()
        state.completed_stages.append("diversity")
        errors = state.validate()
        assert any("chemical_richness is empty" in e for e in errors)
        assert any("shannon_diversity is empty" in e for e in errors)


class TestStageResult:
    """Tests for StageResult dataclass."""

    def test_minimal_result(self) -> None:
        """Test creating minimal stage result."""
        result = StageResult(stage_name="test", success=True, message="Done")
        assert result.stage_name == "test"
        assert result.success is True
        assert result.message == "Done"
        assert result.input_count == 0
        assert result.output_count == 0
        assert result.data is None

    def test_result_with_counts(self) -> None:
        """Test stage result with counts."""
        result = StageResult(
            stage_name="filter",
            success=True,
            message="Filtered",
            input_count=100,
            output_count=50,
        )
        assert result.input_count == 100
        assert result.output_count == 50

    def test_result_with_data(self) -> None:
        """Test stage result with data dict."""
        result = StageResult(
            stage_name="filter",
            success=True,
            message="Done",
            data={"threshold": 0.8},
        )
        assert result.data is not None
        assert result.data["threshold"] == 0.8
