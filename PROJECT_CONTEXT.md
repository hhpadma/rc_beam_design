# RC Beam Design Project Context

## Design Direction

This project is being rebuilt as a lego-style reinforced concrete beam design
system. The core package should stay code-neutral, while ACI, Eurocode, and
future code rules live in separate code packages.

The main design boundary is:

1. Convert loads and forces to actions.
2. Analyze the beam and identify critical sections.
3. Design or review each critical section from its actions.
4. Apply code-specific checks as independent rule modules.

Examples from ACI SP-17 are used as regression tests and references, but the
examples must not decide the architecture.

## Current Workflow

Process-level workflow charts are documented in:

- `docs/WORKFLOW.md`

### Loads to Actions

Code-neutral load conversion lives in:

- `beam_design/core/actions.py`
- `beam_design/beam_loads.py`

`BeamLineActionBuilder` converts surface loads, line loads, and optional
self-weight into line-load actions. Self-weight can be based on a default
section during early design or an explicit section during review.

### Analysis

Analysis is independent of the physical section, except for self-weight already
included in the load/action input.

ACI simplified analysis currently lives in:

- `beam_design/codes/aci318/analysis/simplified.py`

It returns `BeamAnalysisResult` with critical section actions.

Analysis storage is span-aware and tabular:

- `CriticalActionRecord` stores one flexure, shear, torsion, or other action at
  one critical location.
- `SpanActionTable` stores all records for the beam.
- Flexure and shear are stored separately because their critical locations do
  not usually coincide.
- `design_group` links records that should be merged for constructibility, such
  as the right support face of one span and the left support face of the next
  span.

### Section Design

Section design starts from actions:

- bending: mandatory
- shear: mandatory
- torsion: optional

The code-neutral section design entry point is:

- `beam_design/section_designer.py`

`SectionDesignInput` can be created from a critical section returned by
analysis.

### Section Assembly

Section assembly describes the physical section only:

- shape
- clear cover
- longitudinal reinforcement
- transverse reinforcement
- section-specific calculations

It should not own analysis actions.

Relevant modules:

- `beam_design/section_assembler.py`
- `beam_design/core/section_shapes.py`
- `beam_design/reinforcement_assembler.py`
- `beam_design/core/reinforcement.py`

## ACI 318 Progress

Implemented and covered by tests:

- material minimum concrete strength checks
- ACI bar catalog/tag handling
- general rectangle, T, and L section shapes
- ACI effective flange width with guard for flange in tension
- ACI minimum beam depth check
- ACI beam lateral stability check for unbraced beams
- ACI T-beam monolithic/composite construction check
- ACI T-beam flange transverse reinforcement requirement hook
- ACI torsion overhanging flange width check
- ACI calculated deflection requirement hook when minimum depth is not satisfied
- ACI reinforcement tension strain limit hook
- ACI Chapter 21 strength reduction factor table and strain-based phi interpolation
- ACI Table 20.6.1.3.1 specified concrete cover requirements
- ACI 9.7.2.2 and Table 24.3.2 flexural reinforcement distribution check for nonprestressed RC beams with deformed bars
- flexural crack-control spacing checks combine same-elevation detailing groups, so web bars and flange bars are checked as one physical tension-face line
- ACI 25.2.1 longitudinal bar clear spacing check, including explicit-position layers
- SP-17-style web width demonstration helper for checking whether a selected bar count can fit in one web layer
- ACI 24.3.4 T-beam flange tension distribution requirement with the `ln/10` limit and explicit outer-flange reinforcement flag
- explicit-position longitudinal bar layers for detailing cases where bars are not uniformly spaced across the web or flange
- ACI 22.2 flexural/axial design assumptions for report rows and stress block data
- ACI report reference store for non-calculation clauses and SP-17 figure notes
- ACI flexural section design trigger from critical moment design groups
- ACI required-steel solver separated from bar selection and section assembly
- ACI 9.6 minimum flexural reinforcement calculation reused by checks and section design
- ACI same-diameter bar selector for economical provided reinforcement
- ACI flexural strain evaluation for provided bars and phi verification
- Partial section assembly creation with flexural reinforcement only
- action-driven ACI load combinations
- load-to-action conversion for distributed beam loads
- ACI simplified analysis coefficients for moments and shears
- explicit ACI shear critical-plane handling; defaults to support-face shear unless 9.4.3.2 conditions are known
- ACI one-way concrete shear strength calculators for 22.5.5.1, Table 22.5.5.1, 22.5.6.1, Table 22.5.6.1, and 22.5.7.1
- ACI one-way shear design-section evaluation using 22.5.5.1 to decide if stirrup shear strength is required
- ACI 22.5.10.1 required one-way shear reinforcement strength, `Vs >= Vu / phi - Vc`
- ACI 22.5.10.5.3 vertical stirrup shear strength and trial spacing calculation
- ACI Table 9.7.6.2.2 maximum shear reinforcement spacing for nonprestressed RC beams
- ACI 9.6.3.1 minimum shear reinforcement trigger for RC beams, with no exception assumed unless explicitly provided
- ACI Table 19.2.4.2 lambda lookup with explicit interpolation inputs for blend concretes
- ACI Table 20.2.2.4a reinforcement design yield strength limits
- ACI one-way shear requirement checks for 22.5.1.2, 22.5.1.7, 22.5.1.8, 22.5.1.9, and 22.5.3
- critical section action output
- span action table storage with constructibility design groups

Active shear-design flow is limited to nonprestressed reinforced concrete beam
requirements. Prestressed beam, joist-system, steel-fiber, and non-beam
exception branches should not be activated unless the user explicitly adds that
design case later.

Primary test fixture:

- `tests/sp17_examples.py`

Current verification command:

```powershell
pytest -q
```

## Active Package Areas

Use these for new implementation:

- `beam_design/core/`
- `beam_design/codes/aci318/`
- `beam_design/beam_loads.py`
- `beam_design/section_assembler.py`
- `beam_design/section_calculations.py`
- `beam_design/section_designer.py`
- `beam_design/reinforcement_assembler.py`
- `tests/`

## Archived Legacy Modules

Legacy top-level wrappers and old-stage modules are kept under:

- `beam_design/archive/legacy_top_level/`

They are archived to reduce confusion. If useful formulas or ideas are found
there later, integrate them into the new core/code-specific module structure
instead of importing from the archive.
