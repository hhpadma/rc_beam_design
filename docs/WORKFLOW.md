# RC Beam Design Workflow

This document records the process boundaries for the current beam-design
architecture. The charts are intentionally split into smaller workflows so each
process can evolve without turning the system into one large coupled pipeline.

ACI SP-17 examples are used as verification fixtures. They guide test values and
report shape, but they do not own the architecture.

## 1. Overall Process

```mermaid
flowchart TD
    A["Project inputs"] --> B["Loads or direct actions"]
    B --> C["Load-to-action conversion"]
    C --> D["Analysis and critical section extraction"]
    D --> E["Critical action table"]
    E --> F["Section design or section review"]
    F --> G["Reinforcement assembly and detailing"]
    G --> H["Code rule checks"]
    H --> I["Report data and traceable references"]

    B -. "review problem" .-> E
    F -. "physical section instance" .-> G
    G -. "updated physical section instance" .-> H
```

Core rule: analysis belongs to the beam/action system. Section design starts
from actions. Section assembly owns physical geometry, cover, and reinforcement.

## 2. Loads To Actions

```mermaid
flowchart TD
    A["Input loads"] --> B{"Load source"}
    B --> C["Surface loads: psf"]
    B --> D["Line loads: kip/ft"]
    B --> E["Self-weight from section area"]
    C --> F["Tributary conversion"]
    D --> G["Line action"]
    E --> G
    F --> G
    G --> H["Action set by load pattern"]
    H --> I["ACI action-driven load combinations"]
    I --> J["Factored action cases"]

    I --> K["Checks"]
    K --> K1["Combinations are action-driven, not force-reversed"]
    K --> K2["Self-weight is a separate calculation process"]
    K --> K3["Directly supplied actions bypass load derivation"]
```

Important boundary: loads and forces can derive actions, but combined actions
should not be reversed back into loads.

## 3. Analysis And Critical Sections

```mermaid
flowchart TD
    A["Factored line actions"] --> B["Beam spans and support conditions"]
    B --> C{"ACI simplified analysis eligible?"}
    C --> D["Eligibility checks"]
    D --> D1["members are prismatic"]
    D --> D2["loads are uniformly distributed"]
    D --> D3["live load <= 3 dead load"]
    D --> D4["at least two spans"]
    D --> D5["adjacent span difference <= 20 percent"]
    C -->|yes| E["ACI coefficient method"]
    C -->|no| F["External or future analysis engine"]
    E --> G["Moment critical sections"]
    E --> H["Shear critical sections"]
    G --> I["Span action table"]
    H --> I
    I --> J["Design groups for constructibility"]

    H --> H1["Shear critical plane"]
    H1 --> H2["Use distance d from support only when 9.4.3.2 conditions are explicit"]
    H1 --> H3["Otherwise use conservative support-face shear"]
```

Flexure and shear are stored separately because their critical sections usually
do not occur at the same physical location.

## 4. Geometry, Material, And Pre-Design Checks

```mermaid
flowchart TD
    A["Section shape"] --> B["Concrete material"]
    B --> C["Clear cover"]
    C --> D["Pre-design code checks"]

    D --> E["Material requirements"]
    E --> E1["minimum concrete strength"]
    E --> E2["lambda lookup"]

    D --> F["Geometry requirements"]
    F --> F1["minimum beam depth"]
    F --> F2["deflection requirement hook when depth is not enough"]
    F --> F3["effective flange width"]
    F --> F4["guard: skip compression-flange calculation when flange is in tension"]
    F --> F5["T-beam monolithic or composite construction"]

    D --> G["Stability requirements"]
    G --> G1["unbraced length <= 50 times least compression flange or face width"]
    G --> G2["eccentric load warning hook"]

    D --> H["Cover requirements"]
    H --> H1["ACI 20.6.1.3.1 cast-in-place nonprestressed RC beam cover"]
```

The shape module remains code-neutral. ACI can constrain or transform section
metadata, but the physical section remains the shared source of truth.

## 5. Flexural Section Design

```mermaid
flowchart TD
    A["Critical moment action"] --> B["Determine tension face"]
    B --> C["Select compression width"]
    C --> C1["positive moment: flange may be compression zone"]
    C --> C2["negative moment: web usually controls compression block"]
    C --> D["Effective depth from section instance"]
    D --> D1["initial assumption: main bar about 1 in, tie about 1/2 in"]
    D --> E["ACI stress block"]
    E --> E1["epsilon_cu = 0.003"]
    E --> E2["tensile concrete neglected"]
    E --> E3["a = beta1 c"]
    E --> E4["0.85 fc compression stress"]
    E --> F["Required steel solver"]
    F --> G["Minimum flexural reinforcement check"]
    G --> H["Trial bar selection"]
    H --> I["Layer fit and minimum spacing"]
    I --> J["Provided reinforcement"]
    J --> K["Tension strain and phi verification"]
    K --> L["Strength check"]
    L --> M["Partially assembled section for this critical location"]

    G --> G1["ACI 9.6.1 minimum As"]
    K --> K1["ACI 9.3.3.1 strain >= 0.004"]
    K --> K2["ACI 21.2.2 phi from net tensile strain"]
    L --> L1["ACI 9.5.1: phi Mn >= Mu"]
```

The required-steel solver is intentionally small. It receives moment, effective
depth, stress block data, and steel strength. Bar selection and detailing are
separate because constructibility is harder than the strength equation.

## 6. Shear Section Design

```mermaid
flowchart TD
    A["Critical shear action"] --> B["Critical shear plane"]
    B --> C["Concrete shear strength Vc"]
    C --> C1["start with ACI 22.5.5.1 for nonprestressed RC without axial force"]
    C --> C2["optional detailed methods only when inputs are explicit"]
    C --> D["phi for shear"]
    D --> E["Check phi Vc against Vu"]
    E -->|passes| F["Shear reinforcement not required by strength"]
    E -->|fails| G["Required Vs = Vu / phi - Vc"]
    G --> H["Trial stirrup spacing"]
    H --> I["Maximum stirrup spacing"]
    I --> J["Minimum shear reinforcement trigger"]
    J --> K["Shear reinforcement design result"]

    C --> C3["sqrt(fc') limit for shear"]
    G --> G1["ACI 22.5.10.1 required Vs"]
    H --> H1["ACI 22.5.10.5.3 vertical stirrups"]
    H --> H2["Av is effective area of all legs within spacing"]
    I --> I1["ACI Table 9.7.6.2.2 nonprestressed beam spacing"]
    J --> J1["ACI 9.6.3.1 minimum Av trigger"]
    K --> K1["ACI 22.5.1.2 cross-section dimension limit"]
```

Active flow is limited to nonprestressed reinforced concrete beams. Prestressed,
joist, steel-fiber, and non-beam exception branches are intentionally outside
the active design path.

## 7. Reinforcement Detailing

```mermaid
flowchart TD
    A["Provided flexural and shear reinforcement"] --> B{"Layer type"}
    B --> C["Standard layer across web"]
    B --> D["Explicit-position layer"]
    C --> E["Longitudinal bar clear spacing"]
    D --> E
    E --> F["Layer count and cage depth"]
    F --> G["Flexural crack-control spacing"]
    G --> H["T-beam flange tension distribution"]
    H --> I["Transverse reinforcement spacing"]
    I --> J["Cover and bond checks"]
    J --> K["Final physical section instance"]

    E --> E1["ACI 25.2.1 minimum clear spacing"]
    G --> G1["ACI 9.7.2.2 and Table 24.3.2"]
    G --> G2["same-elevation groups are checked together"]
    H --> H1["ACI 24.3.4 distribute flange tension reinforcement within min(bf, ln/10)"]
    H --> H2["outer flange reinforcement required when bf > ln/10"]
    I --> I1["ACI 9.7.6.2.2 shear spacing"]
    J --> J1["ACI 20.6.1.3.1 cover"]
    J --> J2["development length and bond hooks"]
```

The explicit-position layer is the current escape hatch for real detailing
cases such as SP-17 section D-D, where some top tension bars are outside the web
and do not share the same center-to-center spacing as the web bars.

## 8. Reporting Data

```mermaid
flowchart TD
    A["Every calculation or check"] --> B["Numerical result"]
    A --> C["Check status"]
    A --> D["ACI reference"]
    A --> E["Assumptions"]
    B --> F["Report row"]
    C --> F
    D --> F
    E --> F
    F --> G["Tables"]
    F --> H["Narrative calculation steps"]
    F --> I["Future figures and diagrams"]

    G --> G1["required reinforcement table"]
    G --> G2["provided reinforcement and strain table"]
    G --> G3["shear reinforcement table"]
    G --> G4["detailing checks table"]
```

The report layer should consume structured results. It should not recalculate
design values.

## Current Integration Notes

- The current automated suite passes with the active ACI RC beam workflow.
- Flexural strength, shear strength, and detailing checks are connected through
  section design, reinforcement assembly, and rule modules.
- The section instance is the physical source of truth once reinforcement is
  assembled.
- The remaining hard problem is not the strength equations; it is the bar layer
  selector that must choose economical, constructible reinforcement while
  satisfying minimum spacing, maximum crack-control spacing, layer limits, and
  T-beam flange tension distribution.
- TODO: verify the SP-17 design-aid basis for the 11 in center-to-center spacing
  from the outer web bar to the outside-web top bar. The current model records
  it as explicit detailing geometry and checks it, but the exact design-aid
  origin is still open.

