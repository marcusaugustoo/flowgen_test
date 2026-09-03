# FlowGen 0.5b — Multi-Agent Code Generation Research Platform

Experimental research infrastructure for investigating how different multi-agent configurations and local LLM models affect code generation quality. Inspired by the FlowGen paper (SOEN-101, ICSE 2025).

> **Note**: This is NOT a reproduction of the original FlowGen codebase. It is an independent experimental implementation inspired by the methodology described in the paper.

## Quick Start

```bash
# 1. Clone and setup
cd FlowGen_0.5b
python3 -m venv .venv
source .venv/bin/activate
pip install pyyaml requests pytest

# 2. Run tests (no Ollama needed)
python -m pytest tests/ -v

# 3. Run Raw baseline (requires Ollama)
ollama pull qwen2.5-coder:7b
python -m src.main --config config/experiments/raw_baseline.yaml

# 4. Run Waterfall baseline
python -m src.main --config config/experiments/waterfall_baseline.yaml
```

## Architecture

```
flowgen-experiment/
├── config/                    # YAML configuration files
│   ├── default.yaml           # Default parameters
│   └── experiments/           # Per-experiment overrides
├── src/
│   ├── agents/                # Agent implementations
│   │   ├── base_agent.py      # BaseAgent ABC
│   │   ├── requirement_engineer.py
│   │   ├── architect.py
│   │   ├── developer.py
│   │   ├── tester.py
│   │   └── scrum_master.py
│   ├── llm/                   # LLM provider abstraction
│   │   ├── base.py            # BaseLLMProvider ABC
│   │   ├── ollama_provider.py # Ollama REST API
│   │   ├── mock_provider.py   # Testing mock
│   │   └── factory.py         # Provider factory
│   ├── processes/             # Process models
│   │   ├── base.py            # BaseProcess ABC
│   │   ├── raw.py             # Single LLM call (Baseline A)
│   │   ├── waterfall.py       # Sequential agents (Baseline B)
│   │   ├── tdd.py             # Test-driven (Baseline C, stub)
│   │   └── scrum.py           # Sprint-based (Baseline D, stub)
│   ├── orchestration/         # Agent coordination
│   │   ├── orchestrator.py    # Central execution control
│   │   ├── context.py         # SharedContext
│   │   ├── messages.py        # Inter-agent messages
│   │   └── artifacts.py       # Structured artifact storage
│   ├── refinement/            # Self-refinement strategies
│   ├── benchmarks/            # Benchmark loaders (HumanEval)
│   ├── evaluation/            # Test execution & Pass@1
│   ├── results/               # Result persistence & reports
│   └── main.py                # CLI entry point
├── tests/                     # Unit tests (106 tests)
├── datasets/                  # Benchmark data (mini HumanEval)
└── docs/                      # Documentation
```

## Key Design Principles

1. **Configuration-driven**: All experimental parameters live in YAML files
2. **Agents are decoupled**: Agents don't know which process model runs them
3. **LLM is abstracted**: Swap models by changing one config line
4. **Orchestrator controls flow**: Agents never call other agents directly
5. **Everything is logged**: Full traceability of prompts, responses, messages
6. **Never overwrite**: Each experiment gets a unique ID (EXP-NNN)

## Configuring Experiments

All parameters are in `config/default.yaml`. Create overrides in `config/experiments/`:

```yaml
# config/experiments/my_experiment.yaml
experiment:
  name: my_custom_run
  runs: 5

llm:
  provider: ollama
  model: deepseek-coder:6.7b   # Change model here
  temperature: 0.8

pipeline:
  type: waterfall               # raw | waterfall | tdd | scrum

self_refinement:
  enabled: true
  iterations: 3
```

Run it:
```bash
python -m src.main --config config/experiments/my_experiment.yaml
```

## CLI Options

```bash
python -m src.main --config <path>       # Experiment config YAML
python -m src.main --model <name>        # Override model
python -m src.main --process <type>      # Override process (raw/waterfall/tdd/scrum)
python -m src.main --runs <N>            # Override number of runs
```

## Changing the Model

Edit the YAML config:
```yaml
llm:
  provider: ollama
  model: qwen2.5-coder:7b       # ← change this
```

Or via CLI:
```bash
python -m src.main --model llama3.1:8b
python -m src.main --model deepseek-coder:6.7b
python -m src.main --model mistral:7b
```

No code changes needed.

## Process Models

| Process    | Description | Status |
|------------|-------------|--------|
| `raw`      | Single LLM call (Baseline A) | ✅ Implemented |
| `waterfall`| RE → Arch → Dev → Test → Refine (Baseline B) | ✅ Implemented |
| `tdd`      | Tests-first development (Baseline C) | 🏗️ Architecture ready |
| `scrum`    | Sprint-based with Scrum Master (Baseline D) | 🏗️ Architecture ready |

## Agent Pipeline (Waterfall)

```
Problem
  → Requirement Engineer (analyzes, extracts requirements)
  → Architect (designs solution, algorithm)
  → Developer (implements Python code)
  → Tester (generates test cases)
  → Test Execution (sandboxed subprocess)
  → [If failures + refinement enabled]:
      → Developer refinement (fixes based on failure report)
      → Test Execution
      → Repeat up to N iterations
  → Evaluation (Pass@1 against benchmark tests)
```

## Results Structure

```
results/
└── EXP-001_waterfall_baseline/
    ├── config.yaml          # Exact config used
    ├── summary.json         # Aggregated metrics
    ├── report.md            # Markdown results table
    ├── runs/
    │   ├── run_001/
    │   │   ├── results.json # Per-problem pass/fail
    │   │   ├── messages.jsonl
    │   │   └── artifacts/
    │   └── run_002/
    ├── logs/
    └── artifacts/
```

## Adding a New Agent

1. Create `src/agents/my_agent.py`:
```python
from src.agents.base_agent import BaseAgent
from src.llm.base import LLMResponse
from src.orchestration.artifacts import Artifact
from src.orchestration.context import SharedContext

class MyAgent(BaseAgent):
    agent_name = "my_agent"
    agent_role = "My Custom Role"
    artifact_type = "my_output"

    def parse_response(self, response, context):
        return Artifact(type=self.artifact_type, content=response.content, created_by=self.agent_name)

    def update_context(self, context, artifact):
        context.metadata["my_output"] = artifact.content
```

2. Create prompt template: `src/prompts/my_agent/system.txt`

3. Register in `src/agents/factory.py`:
```python
_AGENT_REGISTRY["my_agent"] = "src.agents.my_agent.MyAgent"
```

4. Add to config:
```yaml
agents:
  my_agent: true
```

## Adding a New Process Model

1. Create `src/processes/my_process.py` extending `BaseProcess`
2. Implement `run(context, orchestrator) -> SharedContext`
3. Register in `src/processes/factory.py`
4. Use via config: `pipeline: { type: my_process }`

## Benchmarks

| Benchmark    | Problems | Status |
|-------------|----------|--------|
| HumanEval   | 164      | ✅ Loader ready (mini: 5 problems) |
| MBPP        | 427      | 🏗️ Loader prepared |
| HumanEval-ET| 164      | 🏗️ Loader prepared |
| MBPP-ET     | 427      | 🏗️ Loader prepared |

For the full HumanEval dataset, download and set `benchmark.dataset_path`:
```yaml
benchmark:
  name: humaneval
  dataset_path: datasets/HumanEval.jsonl
```

## Ollama Setup

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start the service
ollama serve

# Pull a model
ollama pull qwen2.5-coder:7b

# Verify
curl http://localhost:11434/api/tags
```

## Running Tests

```bash
# All tests (no Ollama needed — uses MockProvider)
python -m pytest tests/ -v

# Specific module
python -m pytest tests/test_evaluator.py -v

# With coverage
python -m pytest tests/ --cov=src --cov-report=term-missing
```

## Ablation Studies

The architecture supports ablation by toggling agents in config:

```yaml
# Full system
agents: { requirement_engineer: true, architect: true, developer: true, tester: true }

# Without Architect
agents: { requirement_engineer: true, architect: false, developer: true, tester: true }

# Without Tester (no refinement)
agents: { requirement_engineer: true, architect: true, developer: true, tester: false }
```

## License

MIT — For academic research purposes.

## References

- Lin, F., Kim, D.J., & Chen, T.H. (2025). *SOEN-101: Code Generation by Emulating Software Process Models Using Large Language Model Agents*. ICSE 2025.
