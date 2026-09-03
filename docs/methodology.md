# Methodology

## Relationship to FlowGen (SOEN-101)

This implementation is an **experimental research platform inspired by** the FlowGen paper. It is NOT a reproduction of the original code.

### What is Inspired by FlowGen

1. **Multi-agent architecture with SE roles**: Requirement Engineer, Architect, Developer, Tester, Scrum Master
2. **Process model abstraction**: Waterfall, TDD, Scrum as configurable pipelines
3. **Prompt structure**: Role / Instruction / Context format
4. **Self-refinement mechanism**: Generate → Review → Regenerate cycles
5. **Evaluation methodology**: Pass@1 on HumanEval/MBPP benchmarks
6. **Ablation study design**: Removing individual agents to measure impact

### What is Reproduced

1. **Agent roles and responsibilities** (conceptually equivalent)
2. **Waterfall process flow**: RE → Arch → Dev → Test → Refine
3. **Evaluation metric**: Pass@1 with K=1
4. **Experimental conditions**: Zero-shot, temperature 0.8, 5 runs
5. **Benchmark selection**: HumanEval (164 problems)

### What is Modified

1. **LLM backend**: Original uses GPT-3.5; this implementation targets local models (Ollama)
2. **Prompt content**: Prompts are independently designed, not copied from the original
3. **Implementation language**: Independent Python implementation, not based on original source
4. **Configuration system**: YAML-driven configuration for full experimental control
5. **Logging granularity**: Full traceability of every LLM call and agent message

### What is New

1. **MockLLMProvider**: Enables full infrastructure testing without a real LLM
2. **Structured artifact system**: JSON-based artifacts with unique IDs
3. **Message bus**: Complete inter-agent communication recording
4. **Result store**: Auto-incrementing experiment IDs, never-overwrite policy
5. **CLI with overrides**: Command-line parameter overrides for quick experiments
6. **Extensible registry pattern**: Add new agents/processes/providers without modifying existing code

## Experimental Design

### Zero-Shot Approach

All prompts are zero-shot. No few-shot examples are included. This matches the FlowGen paper's primary evaluation methodology.

### No Explicit Chain-of-Thought

Prompts do NOT ask models to expose internal reasoning. Instead, they request structured artifacts (requirements documents, design specifications, code, test cases).

### Temperature

Default temperature is 0.8, matching the FlowGen paper's evaluation settings. This is configurable per experiment.

### Reproducibility

Each experiment produces:
- Unique experiment ID (EXP-NNN)
- Saved configuration (exact YAML used)
- Per-run results with all artifacts and messages
- Aggregated statistics (mean, std, CI)
