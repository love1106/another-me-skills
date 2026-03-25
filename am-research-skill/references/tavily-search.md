
# Tavily Search

Web search via Tavily API with AI-generated answers + source citations.

## Quick Start

```bash
bash scripts/tavily-search.sh "query here"
```

## Usage

```bash
# Basic search (fast, 5 results)
bash scripts/tavily-search.sh "best React frameworks 2026"

# More results
bash scripts/tavily-search.sh "AI trends 2026" 10

# Advanced/deep search (slower, more thorough)
bash scripts/tavily-search.sh "compare Next.js vs Remix performance" 5 advanced
```

## Parameters

| # | Param | Default | Description |
|---|-------|---------|-------------|
| 1 | query | required | Search query |
| 2 | max_results | 5 | Number of results (1-20) |
| 3 | search_depth | basic | `basic` (fast) or `advanced` (deep) |

## Output

JSON with:
- `answer` — AI-synthesized answer
- `results[]` — Array of `{title, url, content, score}`

## When to Use

- **Deep research** — when web_search gives shallow results
- **Fact-checking** — verify claims with multiple sources
- **Market/competitor research** — comprehensive analysis
- **Technical research** — find docs, tutorials, comparisons

## Requirements

- `TAVILY_API_KEY` in `~/.env`
- `curl` and `jq` installed
