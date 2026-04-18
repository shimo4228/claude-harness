#!/usr/bin/env bats

@test "scan.sh exits with 0 when no arguments" {
  run bash "$BATS_TEST_DIRNAME/../scripts/scan.sh"
  [ "$status" -eq 0 ]
}

@test "scan.sh outputs valid JSON" {
  run bash "$BATS_TEST_DIRNAME/../scripts/scan.sh"
  echo "$output" | python3 -m json.tool > /dev/null 2>&1
  [ "$?" -eq 0 ]
}
