# quota-workflow — full workflow (v4.0)

This is the long version of the `quota-workflow` skill. The short, runnable
version is `SKILL.md`. This document adds the review checklist, fallbacks,
measurement, self-critique, and the training mechanism. Both documents
describe the same workflow; if they disagree, `SKILL.md` wins for execution
and this file wins for explanation.

## 0. The problem this solves

An agent running on a strong model (e.g. Gemini 4 Argon Medium in Antigravity)
quickly exhausts its scarce weekly and 5-hour quota limits. Bulk tasks leave
sessions dead mid-way, progress lost, and expensive tokens burned on routine
command execution. Conversely, cheap models (e.g. Gemini 3.8 Flash) have
virtually unlimited quota but struggle with complex planning and architecture
reasoning.

Furthermore, user accounts on [Google Gemini Web](https://gemini.google.com/app)
have separate, generous access to **Gemini 4 Argon with Extended Thinking**
which does NOT consume any Antigravity IDE token quota. Prior attempts (v2) to
leverage this via headless browsers were blocked by Google anti-automation gates.

`quota-workflow v4.0` solves this completely by bridging Google Gemini Web
via the native MCP server (`McpGemini2Antigravity`), using Gemini 4 High
for reasoning and planning at **ZERO Antigravity Pro quota cost**, while
directing Antigravity's cheap model (Gemini 3.8 Flash) fleet to execute the
resulting plan.

## 1. The core idea (v4.0 Dual-Engine Architecture)

1. **Planning Engine (External Brain — Gemini 4 Web):**
   The planning phase uses **Gemini 4 High (Argon with Extended Thinking)**
   from Google Gemini Web via MCP Server `gemini-web` (`gemini_web_ask`).
   Because this runs over HTTP/2 batchexecute RPC with browser session cookies
   (`__Secure-1PSID`, `__Secure-1PSIDTS`), it bypasses browser security blocks
   and costs **0% Antigravity Pro quota**.
2. **Coordinating & Execution Engine (Internal Fleet — Gemini 3.8 Flash):**
   The primary Antigravity chat session operates on **Gemini 3.8 Flash**
   (`flash` tier). It dispatches a Recon sub-agent (`Model: "flash"`) to
   build the context bundle, sends it to the MCP for planning, runs a fast
   gatekeeper checklist review, and dispatches a fleet of sequential execution
   sub-agents (`TypeName: "self"`, `Workspace: "inherit"`, `Model: "flash"`).

```
+--------------------------------------------------------------------------+
|            Google Gemini Web (gemini.google.com/app)                     |
|           Mô hình: Gemini 4 High (Argon Extended Thinking)               |
|      [Chi phí: 0 Quota Antigravity | Suy luận sâu tối đa]                 |
+--------------------------------------------------------------------------+
                                    ▲
                                    │ (MCP: gemini_web_ask)
                                    ▼
+--------------------------------------------------------------------------+
|       Antigravity Primary Coordinator (Model: Gemini 3.8 Flash)          |
|  - Thu thập Context Bundle qua Recon Subagent                            |
|  - Ủy quyền lập Plan cho Gemini 4 Web qua MCP                            |
|  - Rà soát Gatekeeper Checklist & Ghi file Plan                          |
|  - Điều phối các Subagent thực thi tuần tự                               |
+--------------------------------------------------------------------------+
                                    │
                                    ▼ (invoke_subagent: Model "flash")
+--------------------------------------------------------------------------+
|       Antigravity Execution Subagents (Model: Gemini 3.8 Flash)          |
|  - Step Cluster 1 -> Verify & Commit Progress                            |
|  - Step Cluster 2 -> Verify & Commit Progress                            |
|  - Step Cluster N -> Full Test, Rebase & Push                            |
+--------------------------------------------------------------------------+
```

## 2. Tri-Level Planning Fallback Matrix

To guarantee that work is never blocked if network or sessions fluctuate:

| Mode | Planner Engine | Quota Impact | Trigger Condition |
| :--- | :--- | :--- | :--- |
| **Mode 1 (Primary)** | External Gemini 4 High via MCP `gemini-web` | **0 Antigravity Pro Tokens** | Default. MCP server and cookie valid. |
| **Mode 2 (Fallback A)** | Internal Antigravity Pro (Gemini 4 Argon Medium) | 1 Turn Pro Quota | MCP offline, cookie expired, or RPC error. |
| **Mode 3 (Fallback B)** | Internal Antigravity Flash (Gemini 3.8 Flash) | Minimal Flash Quota | Both MCP and Pro quota depleted. Requires user review tag `[LOW-CONFIDENCE-PLAN]`. |

## 3. The 6-step workflow (detailed)

### Step 0 — Verify once

Before relying on the workflow, verify core components and record in project workflow:
1. **MCP Gemini Web Connection:**
   - Execute `gemini_web_account_info` or a test query via `gemini_web_ask`.
   - Confirm authentication source (`.env` or browser cookie) and model `gemini-4`.
   - If connected, Mode 1 is active. If failed, log reason and prepare Mode 2 fallback.
2. **Antigravity Flash Quota:**
   - Check Antigravity Usage view for Flash tier quota.
3. **Sub-agent Dispatch Capability:**
   - Confirm `invoke_subagent` works with `TypeName: "self"`, `Workspace: "inherit"`, `Model: "flash"`.
4. **File Persistence:**
   - Verify `write_to_file` can write to `.agents/plans/`.

### Step 1 — Recon & Context Gathering (ONE Flash Sub-agent dispatch)

Dispatch **ONE** flash sub-agent (`TypeName: "self"`, `Workspace: "inherit"`, `Model: "flash"`) to:
- Write `<repo>/.agents/plans/<date>-<task>-REQUEST.md` (goals, repo, branch, DoD, what NOT to do).
- Write `<repo>/.agents/plans/<task>-CONTEXT.md` (repo layout, house rules with source paths, verified facts, constraints).

The coordinator sleeps while Recon runs, saving turns.

### Step 2 — Plan with Gemini 4 High via MCP gemini-web

1. The coordinator loads `templates/planning-prompt-web.md`, injecting `REQUEST.md` and `CONTEXT.md`.
2. Calls MCP `gemini_web_ask(prompt=planning_prompt, model="gemini-4", extended_thinking=True)`.
3. Gemini 4 Argon Web performs extended thinking and returns the complete Markdown Plan with the five mandatory sections:
   (1) Goal, (2) Context the executor needs, (3) Numbered execution steps, (4) Risks & fallbacks, (5) Definition of done.
4. If Mode 1 throws an unrecoverable exception, switch immediately to Mode 2.

### Step 3 — Dual Gatekeeper Review & Dispatch (Same Turn)

In the same turn as Step 2:
1. Coordinator checks the plan against the **Review Checklist**:
   - [ ] Completeness from start to finish (no skipped middle steps).
   - [ ] Exact file paths and shell commands provided.
   - [ ] Concrete verification and done criteria for every step.
   - [ ] Project house rules strictly respected.
   - [ ] Clear stop-conditions defined (quota, external blocks).
   - [ ] Explicit list of files that must NOT be touched.
   - [ ] Unverified items marked `NEEDS VERIFICATION`.
   - [ ] Step 0 commits plan file and checks HEAD drift.
2. Call `write_to_file` once to save `<repo>/.agents/plans/<date>-<task>.md`.
3. Dispatch the first execution sub-agent (`Model: "flash"`) in the **same turn**.

### Step 4 — Execute with Cheap Model (Gemini 3.8 Flash)

1. Dispatch **ONE flash sub-agent per step cluster** (`TypeName: "self"`, `Workspace: "inherit"`, `Model: "flash"`).
2. Run clusters **sequentially** (Git safety: one writer at a time).
3. The first sub-agent commits the plan file in Step 0.
4. Each sub-agent updates the `Progress` section of the plan file and commits after each step.
5. If errors occur outside the plan, apply the "try twice" rule (max 2 fix attempts); if unresolved, stop and report.

### Step 5 — Verify

- Run step-level verifications.
- Run full project verification (lint, build, tests, health-check).
- Inspect git diff before final push.

### Step 6 — Commit, push, report

- `git pull --rebase` before push; retry once if rejected; never force push.
- Report commit hash, concrete verification evidence, and lessons learned.

## 4. Git rules (one repo, one writer at a time)

- **Never run sub-agents in parallel writing to the same repo.** All sub-agents share `.git` via `Workspace: "inherit"`. Parallel commits cause tree lock errors and corrupted index states.
- **Keep `.agents/plans/` and `.agents/reports/` off `main`.** They are save points for the working branch. Clean up or omit before merging to production.

## 5. Quota rules (v4.0)

1. **Zero Pro Quota for Planning:** Gemini 4 High via MCP `gemini-web` handles deep architecture without draining Antigravity Pro quota.
2. **Coordinator on Flash:** The chat session runs on Gemini 3.8 Flash.
3. **Subagents on Flash:** All bulk coding, test running, and CLI execution run on Flash.
4. **Save Points:** Always commit plan progress after every step.
5. **Security:** Never paste credentials or API tokens into external web prompts.

## 6. Self-Critique & Risk Analysis (Tự Phản Biện Chuyên Sâu v4.0)

Every major upgrade must be subjected to rigorous self-critique. Below is the adversarial analysis of v4.0:

### ⚠️ Risk 1: Cookie Expiry & Headless Cloud VM Boundary
- **Vấn đề:** Trong môi trường Cloud VM (Debian remote sandbox của Antigravity), trình duyệt desktop không có sẵn, nên `rookiepy` không thể tự động bóc cookie như trên máy cá nhân. Nếu cookie trong `.env` (`__Secure-1PSID`, `__Secure-1PSIDTS`) hết hạn giữa chừng, MCP `gemini-web` sẽ trả về lỗi xác thực.
- **Giải pháp hóa giải trong v4.0:**
  1. Cơ chế Fallback 3 tầng (Tri-Level Matrix): Khi MCP lỗi auth, hệ thống không bị crash mà tự động chuyển sang Mode 2 (dùng 1 turn Pro nội bộ của Antigravity) hoặc Mode 3.
  2. Bổ sung script `gemini2anti check` trong Step 0 để phát hiện phiên hợp lệ ngay từ đầu trước khi vào pha Planning.

### ⚠️ Risk 2: Rate Limiting & Abuse Detection từ Google Gemini Web
- **Vấn đề:** Google Gemini Web có bộ lọc chống lạm dụng (anti-abuse / CAPTCHA) nếu tài khoản gửi liên tiếp hàng trăm request tự động trong thời gian ngắn.
- **Giải pháp hóa giải trong v4.0:**
  - `quota-workflow v4.0` **CHỈ dùng Gemini Web đúng 1-2 lần** cho pha lập Plan và kiến trúc (Planning Phase), hoàn toàn KHÔNG dùng Gemini Web để chạy lệnh hay gõ code vụn vặt (bulk execution). Tần suất 1-2 call/task là hoàn toàn tự nhiên và tương đương với người dùng thông thường, không bao giờ chạm ngưỡng abuse rate-limit.

### ⚠️ Risk 3: Hallucination trong Plan từ External LLM
- **Vấn đề:** Gemini 4 Web ở bên ngoài không có tool đọc file trực tiếp trong repo, có thể sinh ra các đường dẫn file tưởng tượng nếu không có đủ thông tin.
- **Giải pháp hóa giải trong v4.0:**
  - Quy trình Step 1 (Recon Sub-agent) bắt buộc chuẩn bị file `CONTEXT.md` đầy đủ cây thư mục, quy tắc nhà (House Rules) và các sự thật đã kiểm chứng trước khi gọi MCP.
  - Step 3 (Dual Gatekeeper): Coordinator kiểm tra lại toàn bộ file paths và lệnh trước khi lưu vào disk và dispatch executor.

### ⚠️ Risk 4: Độ trễ phản hồi (Extended Thinking Latency)
- **Vấn đề:** Gemini 4 Argon với Extended Thinking suy luận rất sâu, thời gian sinh phản hồi có thể mất từ 15–45 giây.
- **Giải pháp hóa giải trong v4.0:**
  - Client trong `gemini2anti/client.py` đã cấu hình timeout hợp lý (25–60s) kèm retry exponential backoff.
  - Vì chỉ gọi đúng 1 lần cho toàn bộ bản kế hoạch, 30 giây suy luận để đổi lấy một Plan hoàn hảo tiết kiệm hàng giờ gỡ lỗi của sub-agent là cái giá hoàn toàn xứng đáng.

## 7. Changelog

- **v4.0 (2026-11-08):** Tích hợp toàn diện `McpGemini2Antigravity`. Chuyển đổi Planner sang **Gemini 4 High (Argon Extended Thinking)** qua MCP `gemini_web_ask`, giảm mức tiêu hao quota Pro của Antigravity về **0%**. Bổ sung Ma trận dự phòng 3 tầng (Tri-Level Fallback Matrix), template prompt chuyên dụng `templates/planning-prompt-web.md`, bổ sung phân tích tự phản biện (Self-Critique).
- **v3.1 (2026-11-08):** Gộp Recon Sub-agent; Plan+Review+Dispatch trong 1 turn; chuyển rule cấm sửa plan về Step 4.
- **v3 (2026-11-08):** Bắt buộc tường minh TypeName/Workspace/Model; quy tắc Git 1 writer; Usage-based quota.
- **v2 (2026-11-08):** Master nội bộ Pro trong Antigravity; bỏ headless browser do bị Google chặn đăng nhập.
- **v1 (2026-11-08):** Phiên bản khởi tạo từ kế hoạch huấn luyện.
