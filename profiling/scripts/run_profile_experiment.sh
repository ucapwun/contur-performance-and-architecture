#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  run_profile_experiment.sh \
    --case LABEL REPOSITORY EXPECTED_REVISION [--case ...] \
    --grid GRID --out-root DIRECTORY --experiment NAME \
    [--repetitions N] [--no-profile] [--no-warm-cache] [-- EXTRA_CONTUR_ARGS...]

The script never checks out or edits source code. Prepare and build one clean
checkout/worktree per revision before running it. With two cases, unprofiled
runs are alternated (A B, B A, A B) to reduce ordering bias. Every cProfile
run is serial because --nomultip is added automatically.
EOF
}

case_labels=()
case_repos=()
case_revisions=()
grid=""
out_root=""
experiment=""
repetitions=3
run_profile=1
warm_cache=1
extra_args=()
has_extra_args=0

while (($#)); do
  case "$1" in
    --case)
      (($# >= 4)) || { usage >&2; exit 2; }
      case_labels+=("$2")
      case_repos+=("$3")
      case_revisions+=("$4")
      shift 4
      ;;
    --grid)
      grid="$2"
      shift 2
      ;;
    --out-root)
      out_root="$2"
      shift 2
      ;;
    --experiment)
      experiment="$2"
      shift 2
      ;;
    --repetitions)
      repetitions="$2"
      shift 2
      ;;
    --no-profile)
      run_profile=0
      shift
      ;;
    --no-warm-cache)
      warm_cache=0
      shift
      ;;
    --)
      shift
      if (($#)); then
        extra_args=("$@")
        has_extra_args=1
      fi
      break
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

((${#case_labels[@]} >= 1 && ${#case_labels[@]} <= 2)) || {
  echo "Provide one or two --case entries." >&2
  exit 2
}
[[ -n "$grid" && -n "$out_root" && -n "$experiment" ]] || {
  usage >&2
  exit 2
}
[[ "$repetitions" =~ ^[1-9][0-9]*$ ]] || {
  echo "--repetitions must be a positive integer." >&2
  exit 2
}
[[ "$experiment" =~ ^[A-Za-z0-9._-]+$ ]] || {
  echo "--experiment may contain only letters, numbers, dot, underscore and hyphen." >&2
  exit 2
}
[[ -d "$grid" ]] || { echo "Grid directory not found: $grid" >&2; exit 2; }
command -v python >/dev/null || { echo "python is not available." >&2; exit 2; }
[[ -x /usr/bin/time ]] || { echo "GNU /usr/bin/time is required." >&2; exit 2; }

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
grid="$(cd -- "$grid" && pwd -P)"
mkdir -p -- "$out_root"
out_root="$(cd -- "$out_root" && pwd -P)"
timestamp="$(date +%Y%m%dT%H%M%S%z)"
result_root="$out_root/${experiment}_${timestamp}"
mkdir -p -- "$result_root/runs" "$result_root/profiles"

# UCL's CentOS 7 nodes provide Git 1.8.3.1, which predates `git -C`.
# Run Git in a subshell instead so the runner works with both old clones and
# newer Git worktrees without changing the caller's working directory.
git_in_repo() {
  local repo="$1"
  shift
  (
    cd -- "$repo"
    git "$@"
  )
}

for index in "${!case_labels[@]}"; do
  label="${case_labels[$index]}"
  repo="${case_repos[$index]}"
  expected="${case_revisions[$index]}"
  [[ "$label" =~ ^[A-Za-z0-9._-]+$ ]] || {
    echo "Invalid case label: $label" >&2
    exit 2
  }
  [[ -d "$repo/.git" || -f "$repo/.git" ]] || {
    echo "Not a Git checkout/worktree: $repo" >&2
    exit 2
  }
  repo="$(cd -- "$repo" && pwd -P)"
  case_repos[$index]="$repo"
  expected_full="$(git_in_repo "$repo" rev-parse "${expected}^{commit}")"
  actual_full="$(git_in_repo "$repo" rev-parse HEAD)"
  [[ "$actual_full" == "$expected_full" ]] || {
    echo "$label HEAD is $actual_full, expected $expected_full" >&2
    exit 2
  }
  git_in_repo "$repo" diff --quiet
  git_in_repo "$repo" diff --cached --quiet
  [[ -x "$repo/bin/contur" || -f "$repo/bin/contur" ]] || {
    echo "Missing Contur entry point: $repo/bin/contur" >&2
    exit 2
  }
  case_revisions[$index]="$expected_full"
done

{
  printf 'experiment\t%s\ncreated\t%s\ngrid\t%s\nyoda_files\t%s\nrepetitions\t%s\n' \
    "$experiment" "$(date --iso-8601=seconds)" "$grid" \
    "$(find "$grid" -type f -name '*.yoda.gz' | wc -l)" "$repetitions"
  printf 'execution_mode\tserial (--nomultip)\nprofile_each_case\t%s\nwarm_cache\t%s\n' \
    "$run_profile" "$warm_cache"
  printf 'extra_contur_args\t'
  if ((has_extra_args == 1)); then
    printf '%q ' "${extra_args[@]}"
  fi
  printf '\n'
} > "$result_root/experiment.tsv"

{
  printf 'case\trepository\trevision\n'
  for index in "${!case_labels[@]}"; do
    printf '%s\t%s\t%s\n' "${case_labels[$index]}" "${case_repos[$index]}" \
      "${case_revisions[$index]}"
  done
} > "$result_root/cases.tsv"

record_environment() {
  local label="$1"
  local repo="$2"
  local revision="$3"
  local source_root="$repo"
  [[ -d "$repo/src/contur" ]] && source_root="$repo/src"
  {
    echo "case=$label"
    echo "timestamp=$(date --iso-8601=seconds)"
    echo "hostname=$(hostname)"
    uname -a
    command -v lscpu >/dev/null && lscpu
    command -v free >/dev/null && free -h
    python --version
    echo "python_executable=$(python -c 'import sys; print(sys.executable)')"
    echo "git_revision=$revision"
    git_in_repo "$repo" status --short --branch
    git_in_repo "$repo" describe --always --tags --dirty
    CONTUR_ROOT="$repo" PYTHONPATH="$source_root${PYTHONPATH:+:$PYTHONPATH}" \
      python -c 'import contur; print("contur_module=" + contur.__file__)'
    CONTUR_ROOT="$repo" PYTHONPATH="$source_root${PYTHONPATH:+:$PYTHONPATH}" \
      python "$repo/bin/contur" --version || true
    command -v rivet >/dev/null && rivet --version || true
    command -v yodals >/dev/null && yodals --version || true
  } > "$result_root/environment_${label}.txt" 2>&1

  local imported_path
  imported_path="$(CONTUR_ROOT="$repo" PYTHONPATH="$source_root${PYTHONPATH:+:$PYTHONPATH}" \
    python -c 'import contur; print(contur.__file__)')"
  case "$imported_path" in
    "$source_root"/*) ;;
    *)
      echo "Rejected $label: imported $imported_path instead of source under $source_root" >&2
      exit 1
      ;;
  esac
}

warm_grid() {
  while IFS= read -r -d '' yoda_file; do
    command cat -- "$yoda_file" >/dev/null
  done < <(find "$grid" -type f -name '*.yoda.gz' -print0)
}

run_case() {
  local index="$1"
  local run_number="$2"
  local kind="$3"
  local label="${case_labels[$index]}"
  local repo="${case_repos[$index]}"
  local source_root="$repo"
  [[ -d "$repo/src/contur" ]] && source_root="$repo/src"
  local run_dir="$result_root/runs/${kind}_${run_number}_${label}"
  mkdir -p -- "$run_dir"
  ((warm_cache == 0)) || warm_grid

  local command_line=(python "$repo/bin/contur" -g "$grid" --nomultip)
  if ((has_extra_args == 1)); then
    command_line+=("${extra_args[@]}")
  fi
  printf '%q ' "${command_line[@]}" > "$run_dir/command.txt"
  printf '\n' >> "$run_dir/command.txt"

  set +e
  (
    export CONTUR_ROOT="$repo"
    export PYTHONPATH="$source_root${PYTHONPATH:+:$PYTHONPATH}"
    cd -- "$run_dir"
    /usr/bin/time -v -o time.txt "${command_line[@]}" >stdout.log 2>stderr.log
  )
  local status=$?
  set -e
  printf '%s\n' "$status" > "$run_dir/exit_status.txt"
  ((status == 0)) || {
    echo "Run failed: $run_dir (exit $status)" >&2
    exit "$status"
  }

  if [[ -f "$run_dir/ANALYSIS/contur_run.db" ]]; then
    python "$script_dir/core_outputs.py" extract \
      "$run_dir/ANALYSIS/contur_run.db" "$run_dir/core_outputs.csv"
  fi
  if [[ -d "$run_dir/ANALYSIS" ]]; then
    (
      cd -- "$run_dir/ANALYSIS"
      find . -type f -printf '%P\t%s\n' | LC_ALL=C sort > "$run_dir/analysis_manifest.tsv"
    )
  fi
}

profile_case() {
  local index="$1"
  local label="${case_labels[$index]}"
  local repo="${case_repos[$index]}"
  local source_root="$repo"
  [[ -d "$repo/src/contur" ]] && source_root="$repo/src"
  local profile_dir="$result_root/profiles/$label"
  local run_dir="$profile_dir/run"
  mkdir -p -- "$run_dir"
  ((warm_cache == 0)) || warm_grid
  local command_line=(python -m cProfile -o "$profile_dir/profile.prof" \
    "$repo/bin/contur" -g "$grid" --nomultip)
  if ((has_extra_args == 1)); then
    command_line+=("${extra_args[@]}")
  fi
  printf '%q ' "${command_line[@]}" > "$profile_dir/command.txt"
  printf '\n' >> "$profile_dir/command.txt"

  set +e
  (
    export CONTUR_ROOT="$repo"
    export PYTHONPATH="$source_root${PYTHONPATH:+:$PYTHONPATH}"
    cd -- "$run_dir"
    /usr/bin/time -v -o "$profile_dir/time.txt" \
      "${command_line[@]}" >"$profile_dir/stdout.log" 2>"$profile_dir/stderr.log"
  )
  local status=$?
  set -e
  printf '%s\n' "$status" > "$profile_dir/exit_status.txt"
  ((status == 0)) || {
    echo "Profile run failed: $profile_dir (exit $status)" >&2
    exit "$status"
  }
  python "$script_dir/profile_summary.py" "$profile_dir/profile.prof" \
    --output-dir "$profile_dir"
  if [[ -f "$run_dir/ANALYSIS/contur_run.db" ]]; then
    python "$script_dir/core_outputs.py" extract \
      "$run_dir/ANALYSIS/contur_run.db" "$profile_dir/core_outputs.csv"
  fi
}

for index in "${!case_labels[@]}"; do
  record_environment "${case_labels[$index]}" "${case_repos[$index]}" \
    "${case_revisions[$index]}"
done

if ((${#case_labels[@]} == 1)); then
  for ((round = 1; round <= repetitions; round++)); do
    run_case 0 "$round" unprofiled
  done
else
  for ((round = 1; round <= repetitions; round++)); do
    if ((round % 2 == 1)); then
      order=(0 1)
    else
      order=(1 0)
    fi
    for index in "${order[@]}"; do
      run_case "$index" "$round" unprofiled
    done
  done
fi

if ((run_profile == 1)); then
  for index in "${!case_labels[@]}"; do
    profile_case "$index"
  done
fi

timing_arguments=()
if ((${#case_labels[@]} == 2)); then
  timing_arguments=(--baseline-label "${case_labels[0]}" --modified-label "${case_labels[1]}")
fi
python "$script_dir/summarise_timings.py" "$result_root" "${timing_arguments[@]}"

comparison_failed=0
if ((${#case_labels[@]} == 2)); then
  mkdir -p -- "$result_root/comparisons"
  for ((round = 1; round <= repetitions; round++)); do
    baseline_csv="$result_root/runs/unprofiled_${round}_${case_labels[0]}/core_outputs.csv"
    modified_csv="$result_root/runs/unprofiled_${round}_${case_labels[1]}/core_outputs.csv"
    comparison_log="$result_root/comparisons/unprofiled_${round}.txt"
    if [[ -f "$baseline_csv" && -f "$modified_csv" ]]; then
      python "$script_dir/core_outputs.py" compare "$baseline_csv" "$modified_csv" \
        >"$comparison_log" 2>&1 || comparison_failed=1
    else
      printf 'MISSING: expected core-output CSV files\n%s\n%s\n' \
        "$baseline_csv" "$modified_csv" >"$comparison_log"
      comparison_failed=1
    fi
  done
  if ((run_profile == 1)); then
    baseline_csv="$result_root/profiles/${case_labels[0]}/core_outputs.csv"
    modified_csv="$result_root/profiles/${case_labels[1]}/core_outputs.csv"
    comparison_log="$result_root/comparisons/profile_runs.txt"
    if [[ -f "$baseline_csv" && -f "$modified_csv" ]]; then
      python "$script_dir/core_outputs.py" compare "$baseline_csv" "$modified_csv" \
        >"$comparison_log" 2>&1 || comparison_failed=1
    else
      printf 'MISSING: expected profile-run core-output CSV files\n%s\n%s\n' \
        "$baseline_csv" "$modified_csv" >"$comparison_log"
      comparison_failed=1
    fi
  fi
fi

if ((comparison_failed == 1)); then
  echo "Experiment completed, but one or more core-output comparisons failed." >&2
  echo "Inspect: $result_root/comparisons" >&2
  exit 1
fi
echo "Completed experiment: $result_root"
