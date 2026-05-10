# Legacy Top-Level Modules

These files were archived during the lego-style rebuild of the beam design
package.

They are kept for reference only. New implementation should live in the active
core and code-specific packages:

- `beam_design/core/`
- `beam_design/codes/`
- `beam_design/section_assembler.py`
- `beam_design/section_designer.py`
- `beam_design/reinforcement_assembler.py`
- `beam_design/beam_loads.py`

If a useful formula or behavior is recovered from this archive, move it into
the new architecture with tests instead of importing from this folder.
