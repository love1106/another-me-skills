# Domain References

Reference files cung cấp domain knowledge cho các loại task cụ thể. **Chỉ đọc khi task match**, không load sẵn để tiết kiệm token.

| Reference | Khi nào đọc | Path |
|-----------|-------------|------|
| Claude CLI Guide | Khi cần details: retry strategy, env setup, session resume, annotation/GitNexus injection | [claude-cli-guide.md](claude-cli-guide.md) |
| Unit Testing | Task viết tests, TDD, hoặc Claude CLI cần viết tests kèm feature | [unit-testing.md](unit-testing.md) |
| Coding Rules | **MỌI task code** — inject tóm tắt vào Claude CLI prompt | [coding-rules.md](coding-rules.md) |
| Tech Stack | User hỏi chọn framework/lib, hoặc agent cần chọn stack cho project mới | [tech-stack.md](tech-stack.md) |
| Landing Page | User yêu cầu build landing page, marketing page, product page | [landing-page.md](landing-page.md) |
| Conventions | Cần check project conventions | [conventions.md](conventions.md) |
| Tunnel Setup | Cần setup Cloudflare tunnel mới | [tunnel-setup.md](tunnel-setup.md) |
| Docker Rules | Task liên quan Docker: deploy, docker-compose, container management | [docker-rules.md](docker-rules.md) |
| Multi-Service Deploy | Deploy project có ≥3 services interdependent, rollback strategy | [multi-service-deploy.md](multi-service-deploy.md) |
| Init Project | Khởi tạo project mới từ template (Step 0) | [init-project.md](init-project.md) |
| Browser Verify | Verify UI frontend qua PinchTab (Step 5.10) | [browser-verify.md](browser-verify.md) |
| Security Review | Security audit codebase (Step 0) | [security-review.md](security-review.md) |
| Dev Preview | Dev preview qua Cloudflare tunnel (Step 7) | [dev-preview.md](dev-preview.md) |
| Self-Improve | Skill tự đánh giá/cải tiến từ dev history (Step 0) | [self-improve.md](self-improve.md) |
| Error Taxonomy | Phân loại error types cho CLI logging (Step 5.8) | [error-taxonomy.md](error-taxonomy.md) |
| Verification Pipeline | Full verification pipeline chi tiết (Step 6) | [verification-pipeline.md](verification-pipeline.md) |
| GitNexus Setup | Install, index, MCP bridge usage, troubleshooting (Step 0c) | [gitnexus-setup.md](gitnexus-setup.md) |
| Lessons Learned | Skill-level learnings, tool quirks, workflow insights | [lessons-learned.md](lessons-learned.md) |

**Cách dùng:**
1. Detect task type từ yêu cầu user
2. Đọc reference file tương ứng (nếu có)
3. Inject nội dung relevant vào prompt cho Claude CLI (Step 5)

> 💡 Thêm reference mới: tạo file trong `references/`, update bảng trên.
