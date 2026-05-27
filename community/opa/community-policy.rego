package tritfabric.community

# Policy stub for Community Learning Plane intake.
# This file is intentionally minimal: it documents the required eligibility
# boundary without claiming an integrated OPA runtime path yet.

default allow_training_use := false

allow_training_use if {
  input.consent == true
  input.license != ""
  count(input.lineage) > 0
  input.rubric_present == true
}

deny_reason contains "missing consent" if {
  input.consent != true
}

deny_reason contains "missing license" if {
  input.license == ""
}

deny_reason contains "missing lineage" if {
  count(input.lineage) == 0
}

deny_reason contains "missing rubric" if {
  input.rubric_present != true
}
