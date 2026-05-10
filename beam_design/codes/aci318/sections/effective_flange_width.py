from dataclasses import dataclass
from enum import Enum

from beam_design.core.model import BeamDesignContext
from beam_design.core.result import CheckResult


class ACIFlangeConfiguration(Enum):
    INTERIOR_T = "interior_t"
    EDGE_L = "edge_l"
    ISOLATED = "isolated"


@dataclass(frozen=True)
class ACIFlangeWidthInput:
    web_width_in: float
    slab_thickness_in: float
    clear_span_in: float
    clear_distance_to_next_beam_in: float | None = None
    configuration: ACIFlangeConfiguration = ACIFlangeConfiguration.INTERIOR_T


def coerce_flange_configuration(value: ACIFlangeConfiguration | str) -> ACIFlangeConfiguration:
    if isinstance(value, ACIFlangeConfiguration):
        return value
    normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
    return ACIFlangeConfiguration(normalized)


def effective_flange_width(data: ACIFlangeWidthInput, flange_in_compression: bool = True) -> float | None:
    if not flange_in_compression:
        return None
    if data.web_width_in <= 0:
        raise ValueError("Web width must be positive.")
    if data.slab_thickness_in <= 0:
        raise ValueError("Slab thickness must be positive.")
    if data.clear_span_in <= 0:
        raise ValueError("Clear span must be positive.")

    if data.configuration == ACIFlangeConfiguration.INTERIOR_T:
        if data.clear_distance_to_next_beam_in is None:
            raise ValueError("Interior T-beam flange width requires clear_distance_to_next_beam_in.")
        each_side = min(
            8.0 * data.slab_thickness_in,
            data.clear_distance_to_next_beam_in / 2.0,
            data.clear_span_in / 8.0,
        )
        return data.web_width_in + 2.0 * each_side

    if data.configuration == ACIFlangeConfiguration.EDGE_L:
        if data.clear_distance_to_next_beam_in is None:
            raise ValueError("Edge L-beam flange width requires clear_distance_to_next_beam_in.")
        overhang = min(
            data.clear_span_in / 12.0,
            6.0 * data.slab_thickness_in,
            data.clear_distance_to_next_beam_in / 2.0,
        )
        return data.web_width_in + overhang

    if data.configuration == ACIFlangeConfiguration.ISOLATED:
        return 4.0 * data.web_width_in

    raise ValueError(f"Unsupported flange configuration: {data.configuration!r}")


@dataclass(frozen=True)
class ACIFlangeWidthCheck:
    check_id: str = "aci318.geometry.effective_flange_width"
    title: str = "Effective flange width"

    def check(self, context: BeamDesignContext) -> CheckResult:
        flange_in_compression = bool(context.metadata.get("aci_flange_in_compression", True))
        if not flange_in_compression:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "Flange is in the tension zone; T/L-beam flange width calculation is not applicable.",
            )

        required_keys = (
            "aci_slab_thickness_in",
            "aci_clear_span_in",
            "aci_clear_distance_to_next_beam_in",
        )
        missing = tuple(key for key in required_keys if key not in context.metadata)
        if missing:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                f"Missing metadata: {', '.join(missing)}.",
            )

        configuration = coerce_flange_configuration(
            context.metadata.get("aci_flange_configuration", ACIFlangeConfiguration.INTERIOR_T)
        )
        data = ACIFlangeWidthInput(
            web_width_in=context.section.width,
            slab_thickness_in=float(context.metadata["aci_slab_thickness_in"]),
            clear_span_in=float(context.metadata["aci_clear_span_in"]),
            clear_distance_to_next_beam_in=float(context.metadata["aci_clear_distance_to_next_beam_in"]),
            configuration=configuration,
        )
        calculated = effective_flange_width(data, flange_in_compression=flange_in_compression)
        provided = context.section.gross_width
        ratio = provided / calculated if calculated else None
        kwargs = {
            "demand": provided,
            "capacity": calculated,
            "ratio": ratio,
            "references": ("ACI 318-14 6.3.2.1",),
            "data": {
                "configuration": configuration.value,
                "web_width_in": data.web_width_in,
                "slab_thickness_in": data.slab_thickness_in,
                "clear_span_in": data.clear_span_in,
                "clear_distance_to_next_beam_in": data.clear_distance_to_next_beam_in,
                "flange_in_compression": flange_in_compression,
            },
        }
        if provided <= calculated:
            return CheckResult.pass_result(self.check_id, self.title, **kwargs)
        return CheckResult.fail_result(self.check_id, self.title, **kwargs)
