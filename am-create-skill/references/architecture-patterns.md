# Architecture Patterns & Complexity Assessment

## Skill Architecture Patterns

### Pattern 1: Simple Skill
```
skill-name/
├── SKILL.md
├── scripts/
├── references/
└── assets/
```
**When**: Single concern, <500 lines total. VD: CDN upload, web search, image generation

### Pattern 2: Reference-Heavy Skill
```
skill-name/
├── SKILL.md              ← Workflow + routing
├── scripts/
└── references/
    ├── topic-a.md
    ├── topic-b.md
    └── topic-c.md
```
**When**: 1 workflow nhưng nhiều domain knowledge. VD: knowledge graph, analytics

### Pattern 3: Orchestrator + Sub-skills ⭐
```
skill-name/                    ← Orchestrator
├── SKILL.md                   ← Entry point: shared rules + routing
├── references/
│   └── shared-rules.md        ← Rules dùng chung across sub-skills
│
├── sub-skill-a/               ← Sub-skill A
│   ├── SKILL.md
│   ├── scripts/
│   └── references/
│
├── sub-skill-b/               ← Sub-skill B
│   ├── SKILL.md
│   ├── scripts/
│   └── references/
│
└── sub-skill-c/               ← Sub-skill C
    ├── SKILL.md
    └── templates/
```
**When**: Multiple phases/modes, >500 lines total, cần scale team, hoặc sub-skills có thể dùng độc lập.

## Orchestrator Pattern — Chi Tiết

### Nguyên tắc

1. **Orchestrator SKILL.md phải nhẹ** (<150 lines)
   - Chỉ chứa: description, shared rules, routing logic
   - KHÔNG chứa chi tiết implementation

2. **Shared rules ở orchestrator, specific rules ở sub-skills**
   - Budget rules, approval gates, thresholds → orchestrator hoặc `references/shared-rules.md`
   - Phase-specific checklists, templates → sub-skill

3. **Sub-skills phải self-contained**
   - Đọc sub-skill SKILL.md = đủ hiểu để execute phase đó
   - Reference ngược orchestrator cho shared rules (không duplicate)

4. **Routing rõ ràng**
   - Orchestrator SKILL.md phải có decision tree: scenario → sub-skill nào
   - Agent đọc orchestrator → biết đọc sub-skill nào tiếp

5. **Customizable per brand/client**
   - Thresholds, targets, rules có thể override per brand
   - Brand config tách riêng: `brands/{slug}/config.md`

### Orchestrator SKILL.md Template

```markdown
---
name: am-{domain}
description: >
  [Mô tả ngắn]. Orchestrates sub-skills for [domain].
  Use when: [triggers].
---

# {Domain} Orchestrator

## Shared Rules
[Rules áp dụng cho TẤT CẢ sub-skills]
- Rule 1: ...
- Rule 2: ...
For detailed shared rules, see `references/shared-rules.md`.

## Routing

| Scenario | Sub-skill | Command |
|---|---|---|
| New client onboard | `onboard/` | Read `onboard/SKILL.md` |
| Analyze performance | `analyze/` | Read `analyze/SKILL.md` |
| Execute & monitor | `operate/` | Read `operate/SKILL.md` |
| Report & iterate | `report/` | Read `report/SKILL.md` |

## Brand Config
Per-brand overrides: `brands/{slug}/config.md`
Override format: same keys as shared rules, brand values take precedence.

## Approval Gates
[Bảng: phase nào cần duyệt, ai duyệt]
```

### Sub-skill SKILL.md Template

```markdown
---
name: am-{domain}-{phase}
description: >
  [Phase description]. Part of am-{domain} orchestrator.
  Use when: [specific triggers for this phase].
---

# {Phase Name}

**Parent**: `am-{domain}/SKILL.md` (shared rules)

## Prerequisites
- [ ] Read parent orchestrator shared rules
- [ ] [Phase-specific prerequisites]

## Workflow
[Phase-specific steps, checklists, templates]

## Scripts
[Phase-specific scripts]

## Output
→ [What this phase produces]
→ Next: [Which sub-skill/phase follows]
```

### Naming Convention

```
Orchestrator:  am-{domain}           VD: am-ads, am-seo
Sub-skills:    am-{domain}-{phase}   VD: am-ads-onboard
```

- Tên phase: verb hoặc noun ngắn (onboard, analyze, operate, report)
- Tối đa 3-5 sub-skills per orchestrator
- Nếu cần >5 → xem lại có merge được không

## Complexity Assessment

Đánh giá mức độ phức tạp **TRƯỚC** khi chọn pattern. 6 chiều, mỗi chiều score 1-4, có weight:

### Scoring Matrix

**D1. Risk & Criticality (×3)** — Sai thì mất gì? Hậu quả nghiêm trọng cỡ nào?
```
1: Low risk       (generate image, organize files, no real consequences)
2: Medium risk    (publish content — minor impact if wrong)
3: High risk      (ads spend, API keys, client-facing output)
4: Critical       (financial transactions, legal, production data, payments)
```

**D2. Knowledge Depth (×2)** — Cần domain expertise bao sâu?
```
1: General       (anyone can do — file ops, simple API calls)
2: Familiar      (common skills — content writing, basic SEO)
3: Specialist    (domain expertise — FB Ads, analytics, medical)
4: Expert        (deep + constantly changing — ad policy, finance regs)
```

**D3. Operational Lifespan (×2)** — Chạy bao lâu?
```
1: One-shot      (run once, done)
2: Short campaign (days-weeks, defined end)
3: Ongoing       (months, no fixed end, periodic review)
4: Indefinite    (years, rules/market change over time)
```

**D4. Feedback Speed (×2)** — Bao lâu mới biết kết quả?
```
1: Instant       (API response, file generated)
2: Fast          (hours-days — ad delivery, email opens)
3: Slow          (weeks-months — SEO rankings, brand awareness)
4: Very slow     (quarters-years — market positioning, LTV)
```

**D5. Decision Complexity (×1)** — Bao nhiêu branches, conditions?
```
1: Linear        (A→B→C, no branches)
2: Some branches (if X do A, else B)
3: Multi-factor  (decision trees, 10+ scenarios)
4: Judgment-heavy (context-dependent, can't fully codify)
```

**D6. Coordination Load (×1)** — Bao nhiêu người/APIs/platforms?
```
1: Solo          (agent only)
2: Pair          (agent + owner)
3: Team          (agent + owner + client/stakeholders)
4: Multi-party   (multiple clients, approval chains, vendors)
```

**D7. Reversibility (×2)** — Hành động có thể undo được không?
```
1: Fully reversible    (draft file, generate image — xóa/tạo lại dễ)
2: Mostly reversible   (publish content — can unpublish, git commit — can revert)
3: Partially reversible (deploy prod — can rollback but downtime, send email — can't unsend)
4: Irreversible        (delete data permanently, execute financial trade, send to external API with side effects)
```

**D8. Verifiability (×2)** — Output có verify tự động được không?
```
1: Auto-verifiable     (build pass/fail, unit test, formal proof, API status code)
2: Semi-auto           (screenshot + visual check, curl + expected response)
3: Human review needed (content quality, design aesthetics, UX flow)
4: Subjective/costly   (open-ended research, brand perception, long-term impact)
```

**D9. Contextuality (×1)** — Cần bao nhiêu sensitive/private context?
```
1: Context-free        (standalone task, no private data needed)
2: Low context         (public repo info, general project structure)
3: Medium context      (API keys, internal configs, user preferences)
4: High context        (PII, financial data, medical records, credentials)
```

### Total Score → Complexity Level

```
Score = D1×3 + D2×2 + D3×2 + D4×2 + D5×1 + D6×1 + D7×2 + D8×2 + D9×1
Range: 16 — 64
```

| Score | Level | Pattern | Improvement Loop |
|---|---|---|---|
| **16-24** | L1 Simple | Pattern 1 | Không cần |
| **25-36** | L2 Moderate | Pattern 2 (references) | Optional — basic tracking |
| **37-50** | L3 Complex | Pattern 3 (orchestrator) | Recommended — tracker + evaluate |
| **51-64** | L4 Critical | Orchestrator + full framework | Bắt buộc — 8 components đầy đủ |

⚠️ **Ranh giới ±2 điểm → dùng judgment, không cứng.**

### What Each Level Requires

**L1 Simple** — SKILL.md đơn giản, chạy xong là xong
```
Required: SKILL.md
Optional: scripts/, references/
```

**L2 Moderate** — Cần references, có thể cần basic tracking
```
Required: SKILL.md, references/
Optional: solution tracking (nếu lifespan ≥3)
```

**L3 Complex** — Orchestrator với sub-skills, có improvement mechanisms
```
Required:
- Orchestrator SKILL.md + routing table
- Sub-skills (self-contained)
- shared-rules.md
- Solution tracker
- Evaluation modes (first-time vs re-evaluate)
- Escalation path

Recommended:
- Adaptive thresholds
- Cross-context learning
- Statistical significance rules
```

**L4 Critical** — Full framework, maximum safety + continuous improvement
```
Required (ALL 8 components):
1. Solution Tracker (propose → measure → learn)
2. Evaluation Modes (first-time vs re-evaluate)
3. Adaptive Thresholds (periodic review + changelog)
4. Cross-Context Learning (Graphiti domain topics)
5. Statistical Significance (min data before decisions)
6. Competitive/External Awareness (regular + trigger-based)
7. Escalation & Timeout (SLA, block handling, exit procedure)
8. Seasonal Planning (calendar + prep timeline, if applicable)

Also required:
- Approval gates (who decides what)
- Kill switches (autonomous protection)
- Per-brand/client config with overrides
- Communication templates
```

### Scoring Examples

**VD 1: Paid Ads Management = 52 → L4 Critical ✅**
```
D1 Risk ×3:         4×3 = 12  (client money at stake)
D2 Knowledge ×2:    3×2 = 6   (specialist — ads platform expertise)
D3 Lifespan ×2:     4×2 = 8   (indefinite, market evolves)
D4 Feedback ×2:     2×2 = 4   (days to see results)
D5 Decisions ×1:    4×1 = 4   (judgment-heavy, context-dependent)
D6 Coordination:    3×1 = 3   (agent + owner + client)
D7 Reversibility ×2:3×2 = 6   (can pause but money already spent)
D8 Verifiability ×2:3×2 = 6   (metrics exist but need human interpretation)
D9 Contextuality:   3×1 = 3   (client budgets, billing, internal targets)
                    TOTAL: 52
```

**VD 2: CDN Upload = 16 → L1 Simple ✅**
```
D1 Risk ×3:         1×3 = 3   (low risk, minor if wrong)
D2 Knowledge ×2:    1×2 = 2   (general — API call)
D3 Lifespan ×2:     1×2 = 2   (one-shot)
D4 Feedback ×2:     1×2 = 2   (instant — upload result)
D5 Decisions ×1:    1×1 = 1   (linear)
D6 Coordination:    1×1 = 1   (solo)
D7 Reversibility ×2:1×2 = 2   (can re-upload anytime)
D8 Verifiability ×2:1×2 = 2   (URL accessible = success)
D9 Contextuality:   1×1 = 1   (no private data)
                    TOTAL: 16
```

### How Dimensions Map to Skill Features

| Dimension High Score → | Skill Needs |
|---|---|
| D1 Risk ≥3 | Approval gates, kill switches, budget caps |
| D2 Knowledge ≥3 | Deep references, domain checklists, use cases, Graphiti ingest |
| D3 Lifespan ≥3 | Improvement loop, state tracking, solution tracker |
| D4 Feedback ≥3 | Longer measurement periods, patience rules, interim metrics |
| D5 Decisions ≥3 | Decision trees, if-then playbooks, scenario-based use cases |
| D6 Coordination ≥3 | SLA, communication templates, escalation path, approval matrix |
| D7 Reversibility ≥3 | Confirmation gates, rollback plan, backup before execute, dry-run mode |
| D8 Verifiability ≤2 | Human review step, iterative feedback loop, subjective criteria guidelines |
| D9 Contextuality ≥3 | Permission declaration, data minimization, privacy guardrails, access scoping |

## Continuous Improvement Framework

Orchestrator skills thực thi dài hạn **PHẢI** có cơ chế tự cải thiện. Áp dụng cho mọi orchestrator skill cần vận hành liên tục.

### 8 Components

#### 1. Solution Tracker (Propose → Measure → Learn)
```
SOL-{NNN}: {Tên}
├── Proposed: YYYY-MM-DD
├── Expected impact: [metric + range cụ thể]
├── Measurement period: [bao lâu đánh giá]
├── Actual result: [data thực tế]
├── Verdict: ✅ SUCCESS | ⚠️ PARTIAL | ❌ FAILED
├── Learning: [bài học]
└── Next action: [continue / adjust / abandon]
```

#### 2. Evaluation Modes
- **FIRST-TIME**: Establish baseline, set benchmarks, create tracker
- **RE-EVALUATE**: Compare actual vs expected, update verdicts, track success rate

#### 3. Adaptive Thresholds
- Monthly review: pull metrics → compare vs thresholds → tighten if better, investigate if worse
- NEVER loosen without understanding root cause
- Log changes: "YYYY-MM-DD: [field] [old]→[new], reason: ___"

#### 4. Cross-Context Learning
- Context-specific: `{context_slug}_{domain}_learnings`
- Domain shared: `{domain}_learnings_general`
- SHARE patterns/insights, DON'T SHARE client data/PII

#### 5. Statistical Significance
- Minimum sample size before conclusions
- Minimum observation period
- One change at a time (avoid confounding)

#### 6. Competitive/External Awareness
- Periodic landscape scan
- Trigger-based check on anomalous metrics

#### 7. Escalation & Timeout
- Define SLA, timeout, fallback, resource protection

#### 8. Seasonal/Cyclical Planning
- Calendar events, prep timeline, post-event review

### Quality Checklist: Improvement Loop

```
IMPROVEMENT LOOP:
- [ ] Solution tracker template exists?
- [ ] Evaluate phase distinguishes first-time vs re-evaluate?
- [ ] Proposals tracked with expected impact + measurement period?
- [ ] Actual results compared vs expected (close the loop)?

ADAPTATION:
- [ ] Thresholds reviewable + changelog mechanism?
- [ ] Statistical significance rules defined?
- [ ] Escalation path for blocked workflows?

LEARNING:
- [ ] Cross-context learning mechanism?
- [ ] Competitive/external awareness cadence?
- [ ] Seasonal planning if applicable?

Score: ___/10
≥8 = Production ready | 5-7 = OK for MVP | <5 = Not ready
```
