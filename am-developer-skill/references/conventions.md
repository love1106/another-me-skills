# Project Conventions Discovery

Before writing any code, discover and follow the project's existing conventions.

## Discovery Checklist

### 1. Check existing config files
```bash
# Code style
cat .editorconfig .prettierrc .eslintrc* tsconfig.json 2>/dev/null

# Project structure
ls -la src/ app/ pages/ components/ services/ 2>/dev/null

# Package manager & scripts
cat package.json | jq '.scripts, .dependencies' 2>/dev/null
```

### 2. Check Claude/AI instructions
```bash
cat .claude/instructions.md CLAUDE.md CODING.md CONVENTIONS.md 2>/dev/null
```

### 3. Analyze existing code patterns
- Look at 2-3 existing files in the same area you'll modify
- Match naming conventions (camelCase, PascalCase, snake_case)
- Match file structure (barrel exports, co-located tests, etc.)
- Match error handling patterns
- Match import ordering

### 4. Check git history for commit style
```bash
git log --oneline -10
```

## Common Patterns at Hubcom

### Git
- **Commits:** Conventional Commits (`feat:`, `fix:`, `chore:`, `refactor:`, `docs:`)
- **Branches:** `feature/`, `fix/`, `refactor/`, `chore/`
- **Never commit to `main` directly**

### When in doubt
- Follow existing code patterns in the repo
- Ask the user before introducing new patterns
- Prefer consistency over "better" approaches
