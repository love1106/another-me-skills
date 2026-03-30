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

## Common Patterns

### Git
- **Commits:** Conventional Commits (`feat:`, `fix:`, `chore:`, `refactor:`, `docs:`)
- **Branches:** `feature/`, `fix/`, `refactor/`, `chore/`
- **Never commit to `main` directly**

### When in doubt
- Follow existing code patterns in the repo
- Ask the user before introducing new patterns
- Prefer consistency over "better" approaches

## Conventional Commits (BẮT BUỘC)

Format: `<type>[optional scope]: <description>`

| Type | Khi nào dùng |
|------|-------------|
| `feat` | Feature mới |
| `fix` | Sửa bug |
| `docs` | Chỉ docs |
| `style` | Format (không đổi logic) |
| `refactor` | Refactor (không fix bug, không thêm feature) |
| `perf` | Performance |
| `test` | Thêm/sửa test |
| `chore` | Build, CI, deps, config |

**Quy tắc chính:**
- Viết thường, imperative mood: `add`, `fix`, `change`
- Không chấm cuối, title ≤ 72 ký tự
- Scope = module/area: `feat(api): add webhook endpoint`
- Breaking change: `feat!: change API response format` + footer `BREAKING CHANGE: ...`

Chi tiết: [conventionalcommits.org](https://www.conventionalcommits.org/en/v1.0.0/)

## Conflict Resolution

1. **Read** — understand both sides of the conflict
2. **Prioritize default branch** — code on default branch is already reviewed, adapt your code to fit
3. **Ask if unsure** — never silently delete someone else's code
4. **Use Claude CLI** for complex conflicts
5. **Never force push to default branch**

## Module System

**Follow project's existing module system.** Prefer ESM cho new projects, nhưng:
- Project dùng CJS (NestJS, v.v.) → dùng CJS cho consistency
- Config files (jest.config.js, .eslintrc.js) thường là CJS — OK
- Không mix ESM và CJS trong cùng 1 project
