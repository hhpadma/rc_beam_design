from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType


class ACIReportReferenceKind(Enum):
    CODE_REQUIREMENT = "code_requirement"
    DESIGN_NOTE = "design_note"
    FIGURE = "figure"


@dataclass(frozen=True)
class ACIReportReference:
    key: str
    clause: str
    title: str
    kind: ACIReportReferenceKind
    text: str
    figure: str | None = None
    tags: tuple[str, ...] = ()


ACI_REPORT_REFERENCES = MappingProxyType(
    {
        "sp17_fig_e1_3_compression_block_locations": ACIReportReference(
            key="sp17_fig_e1_3_compression_block_locations",
            clause="SP-17 Fig. E1.3",
            title="Section compression block and reinforcement locations",
            kind=ACIReportReferenceKind.FIGURE,
            text=(
                "Positive moment uses the effective flange width for compression when the flange is in compression; "
                "negative moment uses the web width when compression is in the web."
            ),
            figure="Fig. E1.3",
            tags=("flexure", "positive_moment", "negative_moment", "compression_block"),
        ),
        "sp17_fig_e1_4_moment_key": ACIReportReference(
            key="sp17_fig_e1_4_moment_key",
            clause="SP-17 Fig. E1.4",
            title="Key to moment design locations",
            kind=ACIReportReferenceKind.FIGURE,
            text=(
                "End-span and interior-span moment labels are used to organize positive and negative "
                "design sections along the continuous beam."
            ),
            figure="Fig. E1.4",
            tags=("flexure", "moment_key", "continuous_beam", "design_sections"),
        ),
        "sp17_first_interior_support_governing_moment": ACIReportReference(
            key="sp17_first_interior_support_governing_moment",
            clause="SP-17 Beam Example 1",
            title="First interior support governing moment",
            kind=ACIReportReferenceKind.DESIGN_NOTE,
            text="The first interior support is designed for the larger of the adjacent support moments.",
            tags=("flexure", "constructibility_group", "support_moment"),
        ),
        "aci_9_5_1_1_required_strength": ACIReportReference(
            key="aci_9_5_1_1_required_strength",
            clause="ACI 318-14 9.5.1.1",
            title="Required strength at each section",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text=(
                "Design strength shall be at least equal to required strength at each section along the member: "
                "phi Mn >= Mu and phi Vn >= Vu."
            ),
            tags=("strength", "flexure", "shear", "design_sections"),
        ),
        "aci_9_5_1_2_phi_from_chapter_21": ACIReportReference(
            key="aci_9_5_1_2_phi_from_chapter_21",
            clause="ACI 318-14 9.5.1.2",
            title="Strength reduction factor source",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text="Strength reduction factor phi shall be determined in accordance with ACI 318-14 Chapter 21.",
            tags=("strength", "phi", "flexure", "design_sections"),
        ),
        "aci_9_4_3_2_shear_critical_section": ACIReportReference(
            key="aci_9_4_3_2_shear_critical_section",
            clause="ACI 318-14 9.4.3.2",
            title="Factored shear critical section",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text=(
                "For nonprestressed beams, shear between the support face and a section d from the face "
                "may be designed for Vu at d only when the support reaction introduces compression, loads "
                "are applied at or near the top, and no concentrated load occurs between the face and d."
            ),
            tags=("strength", "shear", "critical_section", "analysis"),
        ),
        "aci_22_5_1_1_one_way_shear_strength": ACIReportReference(
            key="aci_22_5_1_1_one_way_shear_strength",
            clause="ACI 318-14 22.5.1.1",
            title="One-way shear strength",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text="Nominal one-way shear strength at a section shall be calculated as Vn = Vc + Vs.",
            tags=("strength", "shear", "design_sections"),
        ),
        "aci_22_5_1_2_shear_section_dimension_limit": ACIReportReference(
            key="aci_22_5_1_2_shear_section_dimension_limit",
            clause="ACI 318-14 22.5.1.2",
            title="Cross-sectional dimension limit for shear",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text="Cross-sectional dimensions shall satisfy Vu <= phi(Vc + 8sqrt(fc')bw d).",
            tags=("strength", "shear", "section_dimensions"),
        ),
        "aci_22_5_1_7_web_openings_shear": ACIReportReference(
            key="aci_22_5_1_7_web_openings_shear",
            clause="ACI 318-14 22.5.1.7",
            title="Openings in members",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text="Effect of any openings in members shall be considered in calculating Vn.",
            tags=("strength", "shear", "openings"),
        ),
        "aci_22_5_1_8_creep_shrinkage_axial_tension": ACIReportReference(
            key="aci_22_5_1_8_creep_shrinkage_axial_tension",
            clause="ACI 318-14 22.5.1.8",
            title="Creep and shrinkage axial tension",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text="Effect of axial tension due to creep and shrinkage in restrained members shall be considered in calculating Vc.",
            tags=("strength", "shear", "axial_tension"),
        ),
        "aci_22_5_1_9_variable_depth_shear": ACIReportReference(
            key="aci_22_5_1_9_variable_depth_shear",
            clause="ACI 318-14 22.5.1.9",
            title="Variable-depth inclined flexural compression",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text="Effect of inclined flexural compression in variable-depth members is permitted to be considered in calculating Vc.",
            tags=("strength", "shear", "variable_depth"),
        ),
        "aci_19_2_4_lambda_factor": ACIReportReference(
            key="aci_19_2_4_lambda_factor",
            clause="ACI 318-14 Table 19.2.4.2",
            title="Concrete modification factor lambda",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text="Lambda is selected from aggregate composition; blend values require explicit linear interpolation input.",
            tags=("material", "concrete", "lambda", "shear"),
        ),
        "aci_20_2_2_4a_reinforcement_strength_limits": ACIReportReference(
            key="aci_20_2_2_4a_reinforcement_strength_limits",
            clause="ACI 318-14 Table 20.2.2.4a",
            title="Maximum reinforcement yield strength for design",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text="Maximum fy or fyt used for design calculations depends on usage, application, and reinforcement product.",
            tags=("material", "reinforcement", "shear", "torsion", "flexure"),
        ),
        "aci_22_5_5_1_concrete_shear_no_axial": ACIReportReference(
            key="aci_22_5_5_1_concrete_shear_no_axial",
            clause="ACI 318-14 22.5.5.1",
            title="Concrete shear strength without axial force",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text="For nonprestressed members without axial force, Vc = 2 lambda sqrt(fc') bw d.",
            tags=("strength", "shear", "concrete_shear", "no_axial"),
        ),
        "aci_table_22_5_5_1_concrete_shear_no_axial_detailed": ACIReportReference(
            key="aci_table_22_5_5_1_concrete_shear_no_axial_detailed",
            clause="ACI 318-14 Table 22.5.5.1",
            title="Detailed concrete shear strength without axial force",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text="Detailed Vc for members without axial force is the least of Table 22.5.5.1 expressions (a), (b), and (c).",
            tags=("strength", "shear", "concrete_shear", "no_axial", "detailed"),
        ),
        "aci_22_5_6_1_concrete_shear_axial_compression": ACIReportReference(
            key="aci_22_5_6_1_concrete_shear_axial_compression",
            clause="ACI 318-14 22.5.6.1",
            title="Concrete shear strength with axial compression",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text="For nonprestressed members with axial compression, Vc = 2(1 + Nu/(2000Ag)) lambda sqrt(fc') bw d.",
            tags=("strength", "shear", "concrete_shear", "axial_compression"),
        ),
        "aci_22_5_7_1_concrete_shear_axial_tension": ACIReportReference(
            key="aci_22_5_7_1_concrete_shear_axial_tension",
            clause="ACI 318-14 22.5.7.1",
            title="Concrete shear strength with significant axial tension",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text="For significant axial tension, Vc = 2(1 + Nu/(500Ag)) lambda sqrt(fc') bw d with Nu negative for tension, not less than zero.",
            tags=("strength", "shear", "concrete_shear", "axial_tension"),
        ),
        "aci_22_5_10_1_required_shear_reinforcement": ACIReportReference(
            key="aci_22_5_10_1_required_shear_reinforcement",
            clause="ACI 318-14 22.5.10.1",
            title="Required one-way shear reinforcement",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text="Where Vu exceeds phi Vc, transverse reinforcement shall satisfy Vs >= Vu/phi - Vc.",
            tags=("strength", "shear", "transverse_reinforcement", "required_vs"),
        ),
        "aci_22_5_10_5_transverse_reinforcement_shear_strength": ACIReportReference(
            key="aci_22_5_10_5_transverse_reinforcement_shear_strength",
            clause="ACI 318-14 22.5.10.5.3 through 22.5.10.5.6",
            title="Shear strength provided by transverse reinforcement",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text=(
                "For perpendicular transverse reinforcement, Vs = Av fyt d / s. For inclined stirrups, "
                "Vs = Av fyt(sin alpha + cos alpha)d / s. Av is all effective legs within spacing s, "
                "or twice the bar area for circular ties or spirals."
            ),
            tags=("strength", "shear", "transverse_reinforcement", "provided_vs"),
        ),
        "aci_22_5_3_shear_material_strength_limits": ACIReportReference(
            key="aci_22_5_3_shear_material_strength_limits",
            clause="ACI 318-14 22.5.3.1 through 22.5.3.3",
            title="Shear material strength limits",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text="For one-way shear, sqrt(fc') used for Vc is limited to 100 psi unless permitted, and fy/fyt used for Vs is limited by Table 20.2.2.4a.",
            tags=("strength", "shear", "material_limits"),
        ),
        "sp17_fig_e1_6_shear_at_critical_section": ACIReportReference(
            key="sp17_fig_e1_6_shear_at_critical_section",
            clause="SP-17 Fig. E1.6",
            title="Shear at the critical section",
            kind=ACIReportReferenceKind.FIGURE,
            text="When ACI 9.4.3.2 conditions are satisfied, Vu for shear design is taken at d from the support face.",
            figure="Fig. E1.6",
            tags=("strength", "shear", "critical_section", "sp17"),
        ),
        "aci_21_2_2_moment_axial_phi_by_strain": ACIReportReference(
            key="aci_21_2_2_moment_axial_phi_by_strain",
            clause="ACI 318-14 21.2.2",
            title="Phi for moment and axial force by net tensile strain",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text=(
                "Strength reduction factor for moment, axial force, or combined moment and axial force "
                "is determined from net tensile strain in accordance with Table 21.2.2."
            ),
            tags=("strength", "phi", "flexure", "strain"),
        ),
        "aci_21_2_2_1_compression_controlled_limit": ACIReportReference(
            key="aci_21_2_2_1_compression_controlled_limit",
            clause="ACI 318-14 21.2.2.1",
            title="Compression-controlled strain limit",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text="For deformed reinforcement, epsilon_ty shall be fy/Es; Grade 60 deformed reinforcement may use 0.002.",
            tags=("strength", "phi", "flexure", "strain"),
        ),
        "aci_fig_r21_2_2a_strain_distribution": ACIReportReference(
            key="aci_fig_r21_2_2a_strain_distribution",
            clause="ACI 318-14 Fig. R21.2.2a",
            title="Strain distribution and net tensile strain",
            kind=ACIReportReferenceKind.FIGURE,
            text="Net tensile strain is calculated from the linear strain distribution at nominal strength.",
            figure="Fig. R21.2.2a",
            tags=("flexure", "strain", "figure"),
        ),
        "aci_fig_r21_2_2b_phi_variation": ACIReportReference(
            key="aci_fig_r21_2_2b_phi_variation",
            clause="ACI 318-14 Fig. R21.2.2b",
            title="Variation of phi with net tensile strain",
            kind=ACIReportReferenceKind.FIGURE,
            text="Phi varies from compression-controlled values to 0.90 in the tension-controlled region.",
            figure="Fig. R21.2.2b",
            tags=("strength", "phi", "flexure", "strain", "figure"),
        ),
        "aci_9_5_2_1_moment_low_axial": ACIReportReference(
            key="aci_9_5_2_1_moment_low_axial",
            clause="ACI 318-14 9.5.2.1",
            title="Moment strength for low axial load",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text="For Pu < 0.10fc'Ag, nominal moment strength Mn shall be calculated in accordance with ACI 22.3.",
            tags=("strength", "flexure", "low_axial", "design_sections"),
        ),
        "aci_9_6_1_minimum_flexural_reinforcement": ACIReportReference(
            key="aci_9_6_1_minimum_flexural_reinforcement",
            clause="ACI 318-14 9.6.1.1, 9.6.1.2",
            title="Minimum flexural reinforcement",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text=(
                "Provided tension reinforcement at every beam section shall be at least the larger of "
                "3sqrt(fc')bw d / fy and 200bw d / fy."
            ),
            tags=("strength", "flexure", "minimum_reinforcement", "design_sections"),
        ),
        "aci_9_7_2_2_flexural_reinforcement_distribution": ACIReportReference(
            key="aci_9_7_2_2_flexural_reinforcement_distribution",
            clause="ACI 318-14 9.7.2.2, 24.3.2",
            title="Distribution of flexural reinforcement",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text=(
                "For nonprestressed RC beams, spacing of bonded deformed longitudinal reinforcement closest "
                "to the tension face shall not exceed the Table 24.3.2 deformed-bar spacing limit."
            ),
            tags=("detailing", "flexure", "crack_control", "longitudinal_reinforcement", "beam"),
        ),
        "aci_25_2_1_longitudinal_bar_spacing": ACIReportReference(
            key="aci_25_2_1_longitudinal_bar_spacing",
            clause="ACI 318-14 25.2.1",
            title="Minimum clear spacing of longitudinal bars",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text=(
                "Clear spacing between parallel longitudinal bars in a layer shall be at least the largest "
                "of 1 in., the bar diameter, and 4/3 times the nominal maximum aggregate size."
            ),
            tags=("detailing", "longitudinal_reinforcement", "bar_spacing", "beam"),
        ),
        "aci_24_3_4_t_beam_flange_tension_distribution": ACIReportReference(
            key="aci_24_3_4_t_beam_flange_tension_distribution",
            clause="ACI 318-14 24.3.4",
            title="T-beam flange tension reinforcement distribution",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text=(
                "If T-beam flanges are in tension, bonded flexural tension reinforcement shall be distributed "
                "over the effective flange width, but not wider than ln/10; if bf exceeds ln/10, additional "
                "bonded longitudinal reinforcement is required in the outer flange portions."
            ),
            tags=("detailing", "flexure", "crack_control", "t_beam", "flange_tension", "beam"),
        ),
        "aci_22_3_1_1_flexural_strength_assumptions": ACIReportReference(
            key="aci_22_3_1_1_flexural_strength_assumptions",
            clause="ACI 318-14 22.3.1.1",
            title="Nominal flexural strength assumptions",
            kind=ACIReportReferenceKind.CODE_REQUIREMENT,
            text="Nominal flexural strength Mn shall be calculated in accordance with the assumptions of ACI 22.2.",
            tags=("strength", "flexure", "assumptions", "design_sections"),
        ),
    }
)


def report_reference(key: str) -> ACIReportReference:
    return ACI_REPORT_REFERENCES[key]


def report_references_by_tag(tag: str) -> tuple[ACIReportReference, ...]:
    return tuple(reference for reference in ACI_REPORT_REFERENCES.values() if tag in reference.tags)


def report_reference_rows() -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "key": reference.key,
            "clause": reference.clause,
            "title": reference.title,
            "kind": reference.kind.value,
            "text": reference.text,
            "figure": reference.figure,
            "tags": reference.tags,
        }
        for reference in ACI_REPORT_REFERENCES.values()
    )
