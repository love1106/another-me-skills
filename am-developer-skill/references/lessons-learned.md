# Lessons Learned — Developer Skill

**Skill-level** learnings — cách dùng skill, workflow insights, tool quirks.
Khác với **annotations** (project-level gotchas lưu trong `memory/hc-developer-skill-annotations/<project>.jsonl`).

- **Lessons Learned** = "spawn.sh cần setfacl" (áp dụng mọi project)
- **Annotations** = "Orchestrator phải docker compose up --build" (project-specific)

| # | Lesson | Context |
|---|--------|---------|
| 1 | **`spawn.sh` cần setfacl/chmod workdir** — user `coder` không access được dir owned by root | Test task 2026-03-14: files tạo sai chỗ (`/tmp/src/` thay vì workdir) |
| 2 | **`--permission-mode bypassPermissions` blocked for root** — phải dùng `su - coder` | Claude Code CLI restriction |
| 3 | **`--permission-mode acceptEdits`** là alternative khi không dùng được `bypassPermissions` — nhưng sẽ hỏi confirm cho commands | Fallback option, chưa cần |
| 4 | **Per-project annotations = learning loop** — gotchas persist qua sessions, auto-inject vào prompt. Dùng `annotate.sh inject` (Step 5.2) + `annotate.sh add` (Step 5.9) | Inspired by Context Hub (andrewyng). 2026-03-19 |
| 5 | **Python heredoc + positional args = broken** — `python3 << 'EOF' "$arg"` treats arg as filename. Dùng env vars: `_PY_VAR="$val" python3 << 'EOF'` | annotate.sh refactor. 2026-03-19 |
| 6 | **JSONL must be fault-tolerant** — 1 corrupted line crashes toàn bộ command. Luôn wrap `json.loads()` trong try/except | annotate.sh round 2. 2026-03-19 |
| 7 | **Multi-commit squash** — Claude CLI có thể tạo nhiều commits. `git reset --soft` + re-commit thay vì amend (chỉ fix commit cuối) | Step 8 fix. 2026-03-19 |
| 8 | **Task size gates everything** — Quick/Medium/Large/Hotfix quyết định workflow depth. Quick = skip annotations heavy inject, skip browser verify trivial, skip verification full. Không one-size-fits-all | Simulation round 3. 2026-03-19 |
| 9 | **Annotations need guardrails** — auto-dedup (≥80% word overlap), text truncate 500 chars, size limits. Không để agent dump stack traces làm annotation | Adversarial round 4. 2026-03-19 |
| 10 | **Claude CLI smart quotes** — CLI đôi khi dùng `''` (U+2018/2019) trong JS strings → syntax error. Detect + sed/python replace sau mỗi spawn nếu output có JS/TS files | another-me star-office-ui. 2026-03-17 |
| 11 | **Mega-prompt = stuck typing** — gom task lớn vào 1 prompt → chạy 10-15 phút → không report progress → user thấy typing mãi. PHẢI chia subtask 1-2 phút, report sau mỗi cái | Bug report anh Khôi. 2026-03-19 |
| 12 | **Chủ quan = quality thấp** — skip plan/discuss → implement sai approach. Skip verify → miss bugs. Hard Rule #7: PHẢI discuss solution trước (Step 1b), PHẢI self-review sau (Step 6). Khi không chắc Quick/Medium → default Medium | Feedback anh Khôi. 2026-03-23 |
| 13 | **Parallel sessions overlap = disaster** — 2+ sessions cùng `cd` vào 1 repo folder → git conflict, stash mất, build race. PHẢI dùng `worktree.sh acquire` (Step 4) để tự tạo worktree khi repo busy. LUÔN `release` sau khi xong (Step 8b) | Feedback anh Khôi. 2026-03-25 |
| 14 | **spawn.sh cần timeout** — Claude CLI có thể hang vô tận. Default 180s, exit code 124 = timed out. Không tăng timeout — chia task nhỏ hơn | Self-improve. 2026-03-25 |
| 15 | **Scope drift = silent bug** — Claude CLI đôi khi sửa file ngoài scope (tự ý refactor, thêm import). Self-review PHẢI check `git diff --name-only` vs Step 3 plan. File ngoài scope → revert hoặc justify | Self-improve. 2026-03-25 |
| 16 | **Deploy = separate step** — skill dừng ở PR creation, quên deploy. Step 9 cho phép detect + chạy deploy method phù hợp sau merge. Luôn confirm user trước khi deploy prod | Self-improve. 2026-03-25 |
| 17 | **Scout trước Plan** — discuss approach mà chưa đọc code = đoán mò. Step 1a (Scout) bắt buộc: reproduce → locate → root cause → blast radius → evidence. Solution dựa trên code thật, không giả định | Feedback anh Khôi. 2026-03-25 |
