===================================================
PPCU TestBench - Tool Scripts Documentation
===================================================

1. Tool Overview
-----------------
This directory contains utility scripts for generating
YAML protocol definitions from Excel and fixing tests.

  gen_yaml.py        - Generate telemetry YAML from Excel
  generate_enums.py  - Generate enums.yaml + update telemetry YAMLs
  parse_excel.py     - Extract and verify Excel content
  fix_tests.py       - Auto-fix test assertions for new YAML IDs
  fix_enum_tests.py  - Fix test assertions for enum resolution

2. Bit Offset Conversion
-------------------------
Excel uses frame-level bit offsets (bit 0 = frame byte 0).
Code uses data-field byte offsets (byte 0 = frame byte 8).
Conversion formula:

  data_offset = bit_offset / 8 - 8
  bit_in_byte = bit_offset % 8

Example: bit_offset=104 -> byte=13 -> data_offset=5
         TM1005 at data_offset=5, bit_offset=0, bit_length=4

3. Regenerating YAML from Excel
---------------------------------
python tools/gen_yaml.py

This reads PPCU_Telemetry_Database_v2.xlsx and writes:
  protocol_defs/nebula_ppcu/telemetry_tm1.yaml
  protocol_defs/nebula_ppcu/telemetry_tm2.yaml
  protocol_defs/nebula_ppcu/telemetry_query.yaml

4. Regenerating Enums
-----------------------
python tools/generate_enums.py

This reads column 13 (enum descriptions) from the Excel,
generates protocol_defs/nebula_ppcu/enums.yaml, and updates
all three telemetry YAML files with enum_ref values.

5. Parameter ID Naming
-----------------------
TM1xxx - TM1 telemetry parameters
TM2xxx - TM2 telemetry parameters
TM3xxx - Query packet parameters

Previous IDs (TMHEDTZxxxx) are deprecated.

6. Adding New Parameters
-------------------------
1. Add rows to the Excel spreadsheet
2. Run tools/gen_yaml.py to regenerate YAML
3. Run tools/generate_enums.py to update enum YAML
4. Run tests to verify

7. File Structure
-------------------
tools/
  README.txt           - This documentation
  gen_yaml.py          - YAML generator from Excel
  generate_enums.py    - Enum YAML generator
  parse_excel.py       - Excel data dumper
  fix_tests.py         - Test auto-fixer
  fix_enum_tests.py    - Enum test auto-fixer

protocol_defs/nebula_ppcu/
  telemetry_tm1.yaml   - TM1 parameter definitions (47 params)
  telemetry_tm2.yaml   - TM2 parameter definitions (86 params)
  telemetry_query.yaml - Query packet definitions (105 params)
  enums.yaml           - Enum value definitions

config/
  products.yaml        - Product registry
  default.yaml         - Default configuration

tests/
  test_protocol.py     - Unit tests (25 tests)
  test_comms.py        - Integration tests (6 tests)
