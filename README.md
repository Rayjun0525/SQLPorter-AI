# SQLPorter-AI

An intelligent SQL conversion tool that transforms Oracle SQL into PostgreSQL using multi-agent LLM collaboration and transformation knowledge memory.

## Additional Settings
From fast-agent code, it must be altered `.local/lib/python3.12/site-packages/mcp_agent/llm/providers/augmented_llm_openai.py` file.  
```python
def _initialize_default_params(self, kwargs: dict) -> RequestParams:
       """Initialize OpenAI-specific default parameters"""
       chosen_model = kwargs.get("model", DEFAULT_OPENAI_MODEL)
       max_tokens = kwargs.get("max_tokens", 10000) ## add this param
       return RequestParams(
           model=chosen_model,
           systemPrompt=self.instruction,
           parallel_tool_calls=True,
           max_iterations=10,
           use_history=True,
           maxTokens=max_tokens, ## add this param
       )
```

---

## 📦 Installation

### Prerequisites

| Tool     | Install |
|----------|---------|
| uv       | curl -LsSf https://astral.sh/uv/install.sh | sh |
| python3.12+ | Install via system package manager |
| fast-agent-mcp | `uv pip install fast-agent-mcp` |

### Install dependencies

```bash
uv pip install -r requirements.txt
```

---

## 🚀 Usage

### Step 1. Prepare your Oracle SQL

Place your `.sql` files inside the `ASIS/` folder.  
Subdirectories are supported and preserved in the output.

```bash
ASIS/
└── team/
    └── user.sql
```

### Step 2. Run the conversion

```bash
python main.py
```

> By default, this uses `fastagent.config.yaml` in the current directory.

### Step 3. Review results

- Converted files will be saved in `TOBE/` with `_ported.sql` suffix.
- Summary reports:
  - JSON: `reports/result_summary.json`
  - HTML: `reports/result_summary.html`

---

## ⚙️ Configuration (`fastagent.config.yaml`)

### Example

```yaml
sqlporter:
  models:
    converter_1: "generic.gemma3:4b"
    converter_2: "generic.llama3.2:3b"
    converter_3: "openai.gpt-4o-mini"

  paths:
    input_dir: "./ASIS"
    output_dir: "./TOBE"
    report_dir: "./reports"

  settings:
    max_refinements: 3
    min_rating: "EXCELLENT"
    retry_limit: 3
    comment_prefix: "--"
```

> You can override any setting using the CLI:
```bash
python main.py --config path/to/your_config.yaml
```

---

## 🧠 Knowledge-Based Transformation

The tool remembers successful transformations and suggests them to the model in future executions, increasing conversion accuracy over time.

Stored in:
```
knowledge/transformations.json
```

---

## 🧪 Testing

Unit tests included:

```bash
pytest tests/
```

---

## 📁 Project Structure

```
sqlporter/
├── ASIS/         # Input SQL
├── TOBE/         # Converted SQL output
├── reports/      # JSON + HTML reports
├── knowledge/    # Transformation memory
├── config/       # Config loader + logging
├── core/         # App, runner, file_io, knowledge
├── agents/       # Converters, evaluator, merge, pipeline
├── main.py       # Typer CLI entrypoint
├── fastagent.config.yaml
```

---

## 🧩 Sample Output

### HTML Report

![example_report](docs/report_example.png)

---

## License

MIT (or internal)
