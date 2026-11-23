# Validation oracle

The public entry point is `taskforge validate`. A valid run prints a JSON object with `"status": "valid"` and exits 0. A rejected file prints `code: message` on stderr and exits 2.

| Fixture | Expected code |
| --- | --- |
| `src/taskforge/data/dataset.json` with `general_trace.json` and `costs/demo.json` | valid |
| `invalid/repeated_ids.json` | `duplicate_id` |
| `invalid/leaked_family.json` | `template_family_leak` |
| `invalid/mixed_labels.json` | `label_dictionary_mismatch` |
| `invalid/missing_general_dataset.json` plus `missing_general_trace.json` | `missing_general_result` |
| `invalid/bad_schema.json` | `unsupported_schema_version` |
| `invalid/oversized_text.json` | `input_too_large` |
| `invalid/float_money.json` | `money_type` |

Money fields are decimal strings. A JSON number is rejected even when it looks like 0.005, because that literal is not a decimal quantity.
