# Experiment Protocol

## Objective

Investigate how different multi-agent configurations and local LLM models affect code generation quality, as measured by Pass@1 on standard benchmarks.

## Independent Variables

| Variable | Values | Notes |
|----------|--------|-------|
| LLM Model | qwen2.5-coder:7b, llama3.1:8b, deepseek-coder:6.7b, mistral:7b | Local models via Ollama |
| Process Model | raw, waterfall, tdd, scrum | Pipeline topology |
| Number of Agents | 0 (raw), 4 (waterfall), 5 (scrum) | Agent count per process |
| Refinement | enabled/disabled, iterations (0-5) | Self-refinement cycles |
| Temperature | 0.8 (default), others as needed | LLM sampling temperature |
| Agent Ablation | Full, -RE, -Arch, -Tester, -Refinement | Removed components |

## Dependent Variables

| Variable | Metric | Description |
|----------|--------|-------------|
| Functional Correctness | Pass@1 | Fraction of problems passing all tests on first attempt |
| Code Quality | Code smells (future) | Pylint/flake8 analysis of generated code |
| Exception Handling | Handled exceptions (future) | Count of try/except blocks |
| Computational Cost | LLM calls | Total API calls per problem |
| Token Usage | Tokens in/out | Input and output token counts |
| Execution Time | Wall-clock time (ms) | Total pipeline execution time |
| Refinement Impact | Pass before/after | Pass rate change after refinement |

## Controls

1. **Seed**: When set, ensures reproducible sampling (model-dependent)
2. **Temperature**: Fixed at 0.8 across all experiments unless explicitly varied
3. **Prompts**: Identical prompt templates across all models (zero-shot)
4. **Benchmark**: Same problem set for all configurations
5. **Evaluation**: Same test executor, timeout (30s), and metric computation

## Experimental Conditions

### Baseline A — Raw Model
```yaml
pipeline: { type: raw }
agents: { all: false }
refinement: { enabled: false }
```

### Baseline B — Waterfall
```yaml
pipeline: { type: waterfall }
agents: { requirement_engineer: true, architect: true, developer: true, tester: true }
refinement: { enabled: true, iterations: 3 }
```

### Baseline C — TDD (future)
```yaml
pipeline: { type: tdd }
```

### Baseline D — Scrum (future)
```yaml
pipeline: { type: scrum }
agents: { scrum_master: true, ... }
```

## Number of Runs

- **Primary evaluation**: 5 runs per configuration (matching FlowGen paper)
- **Quick validation**: 1 run
- **Statistical analysis**: Mean and standard deviation reported

## Benchmark

- **Primary**: HumanEval (164 problems)
- **Validation**: HumanEval mini (5 problems)
- **Extended**: MBPP (427 problems), HumanEval-ET, MBPP-ET (future)

## Metric: Pass@1

Pass@1 = (number of problems with correct code on first attempt) / (total problems)

Where "correct" means the generated code passes ALL canonical tests for that problem.

K=1 is the strictest evaluation: only one attempt per problem per run.

## Result Storage

```
results/EXP-NNN_<name>/
├── config.yaml         # Exact configuration
├── summary.json        # Aggregated metrics
├── report.md           # Human-readable table
└── runs/run_NNN/       # Per-run data
```

## Criteria for Success

An experiment is considered valid when:
1. All benchmark problems were attempted
2. Code execution did not timeout for >10% of problems
3. Results are reproducible (same config → similar Pass@1 within std)
4. All artifacts and messages are persisted

## Threats to Validity

### Internal Validity
- **Prompt bias**: Prompts may favor certain model architectures
- **Token limits**: Smaller models may truncate long contexts
- **Temperature sensitivity**: Results may vary significantly with temperature

### External Validity
- **Benchmark scope**: HumanEval focuses on algorithmic problems, not full applications
- **Model selection**: Results specific to tested model sizes/architectures
- **Local execution**: Performance depends on hardware (GPU/CPU)

### Construct Validity
- **Pass@1 limitations**: Does not measure partial correctness or code quality
- **Test coverage**: Benchmark tests may not cover all edge cases

### Reliability
- **Stochastic generation**: LLM outputs vary between runs
- **Mitigation**: Multiple runs (5) with statistical reporting
