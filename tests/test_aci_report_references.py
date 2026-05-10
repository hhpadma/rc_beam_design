import pytest

from beam_design.codes.aci318 import (
    ACIReportReferenceKind,
    ACI_REPORT_REFERENCES,
    report_reference,
    report_reference_rows,
    report_references_by_tag,
)


def test_report_references_store_non_calculation_code_material():
    reference = report_reference("aci_9_5_1_1_required_strength")

    assert reference.clause == "ACI 318-14 9.5.1.1"
    assert reference.kind == ACIReportReferenceKind.CODE_REQUIREMENT
    assert "phi Mn >= Mu" in reference.text
    assert "phi Vn >= Vu" in reference.text


def test_report_references_can_be_selected_by_tag_for_flexure_reports():
    flexure_references = report_references_by_tag("flexure")
    keys = {reference.key for reference in flexure_references}

    assert "sp17_fig_e1_3_compression_block_locations" in keys
    assert "sp17_fig_e1_4_moment_key" in keys
    assert "aci_9_5_1_1_required_strength" in keys
    assert "aci_9_5_1_2_phi_from_chapter_21" in keys
    assert "aci_21_2_2_moment_axial_phi_by_strain" in keys
    assert "aci_fig_r21_2_2a_strain_distribution" in keys
    assert "aci_fig_r21_2_2b_phi_variation" in keys
    assert "aci_9_5_2_1_moment_low_axial" in keys
    assert "aci_22_3_1_1_flexural_strength_assumptions" in keys


def test_report_reference_rows_are_table_friendly():
    rows = report_reference_rows()

    assert len(rows) == len(ACI_REPORT_REFERENCES)
    assert rows[0]["key"]
    assert rows[0]["clause"]
    assert isinstance(rows[0]["tags"], tuple)


def test_report_reference_table_is_immutable():
    with pytest.raises(TypeError):
        ACI_REPORT_REFERENCES["new"] = report_reference("aci_9_5_1_1_required_strength")
