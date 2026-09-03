# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────┐
│                    CLI / Main                        │
│              (config loading, arg parsing)            │
├─────────────────────────────────────────────────────┤
│                  Orchestrator                        │
│          (controls agent execution flow)             │
├──────────┬──────────┬──────────┬────────────────────┤
│ Process  │  Agent   │  LLM     │   Evaluation       │
│ Models   │  Layer   │  Layer   │   Layer            │
├──────────┼──────────┼──────────┼────────────────────┤
│ Raw      │ RE       │ Ollama   │ TestExecutor       │
│ Waterfall│ Architect│ Mock     │ Evaluator          │
│ TDD      │ Developer│ (OpenAI) │ Pass@1             │
│ Scrum    │ Tester   │          │ Statistics         │
│          │ Scrum M. │          │                    │
├──────────┴──────────┴──────────┴────────────────────┤
│              Shared Infrastructure                   │
│  SharedContext │ MessageBus │ ArtifactStore          │
│  ResultStore   │ LLMCallLogger │ Benchmark          │
└─────────────────────────────────────────────────────┘
```

## Key Abstractions

### 1. LLM Provider (src/llm/)
- `BaseLLMProvider` → `OllamaProvider`, `MockLLMProvider`
- Decouples agents from specific LLM implementations
- Built-in metric tracking (calls, tokens, latency)

### 2. Agent (src/agents/)
- `BaseAgent` → `RequirementEngineer`, `Architect`, `Developer`, `Tester`, `ScrumMaster`
- Loads prompt templates from `src/prompts/`
- Produces structured `Artifact` objects
- Updates `SharedContext` with its output

### 3. Process Model (src/processes/)
- `BaseProcess` → `RawProcess`, `WaterfallProcess`, `TDDProcess`, `ScrumProcess`
- Defines agent execution order and transitions
- Controls refinement loops
- Agent does NOT know which process is running it

### 4. Orchestrator (src/orchestration/)
- Central controller that invokes agents via process model
- Records all messages (`MessageBus`) and artifacts (`ArtifactStore`)
- Agents never call other agents — always through orchestrator

### 5. SharedContext (src/orchestration/context.py)
- Accumulates artifacts as pipeline progresses
- Per-agent context filtering: each agent sees only relevant fields
- Serializable for persistence and debugging

### 6. Evaluation (src/evaluation/)
- `TestExecutor`: Sandboxed code execution via subprocess
- `Evaluator`: Runs generated code against benchmark tests
- `Pass@1`: Primary metric computation
- `Statistics`: Mean, std, CI across runs

## Data Flow

```
ExperimentConfig (YAML)
        │
        ▼
    LLMFactory ──────► LLMProvider
        │
        ▼
    ProcessFactory ──► ProcessModel
        │
        ▼
    Orchestrator
        │
        ├── for each Problem:
        │       │
        │       ▼
        │   SharedContext(problem)
        │       │
        │       ▼
        │   ProcessModel.run()
        │       │
        │       ├── Agent1.execute(context) → Artifact → Context
        │       ├── Agent2.execute(context) → Artifact → Context
        │       ├── ...
        │       └── [Refinement loop]
        │
        ▼
    Evaluator
        │
        ▼
    ResultStore (EXP-NNN/)
```

## Extension Points

| What to Add | Where | How |
|------------|-------|-----|
| New LLM provider | `src/llm/` | Extend `BaseLLMProvider`, register in factory |
| New agent | `src/agents/` | Extend `BaseAgent`, add prompt template, register |
| New process model | `src/processes/` | Extend `BaseProcess`, register in factory |
| New benchmark | `src/benchmarks/` | Extend `BaseBenchmark`, register in loaders |
| New refinement strategy | `src/refinement/` | Extend `BaseRefinementStrategy` |
| New metric | `src/evaluation/` | Add to `statistics.py` or create new module |
