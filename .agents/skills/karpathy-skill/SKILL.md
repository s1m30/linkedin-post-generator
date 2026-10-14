---
name: karpathy
description: Use these four core principles to write clean, readable and maintainable code.
---

<!-- Tip: Use /create-skill in chat to generate content with agent assistance -->

# Karpathy AI Developer Guidelines

## 1. Think Before Coding
- Before writing any code or proposing edits, you MUST think step-by-step.
- Output a brief "Plan" explaining your interpretation of the task, edge cases, and any trade-offs.
- If the user's request is ambiguous, stop and ask clarifying questions. Do not guess.
- Actively push back if a simpler, more optimal path exists than what was requested.

## 2. Simplicity First
- Prioritize minimalism. Write the absolute minimum amount of code required to solve the exact problem.
- DO NOT add speculative features, unrequested abstractions, boilerplate "future-proofing," or single-use helper functions.
- If a 200-line implementation can be safely refactored into 50 lines, do it.

## 3. Surgical Changes
- Do not engage in "drive-by refactoring." Limit your git diff strictly to the requested feature or fix.
- Match the exact syntax, style, formatting, and naming conventions of the surrounding codebase, even if you consider them suboptimal.
- Only clean up code messes that your own new changes directly introduce.

## 4. Goal-Driven Execution
- When asked to fix a bug or implement a feature, always establish success criteria.
- Prefer a test-driven approach: read existing tests, ask or assist to write a reproducing test case first, execute it, apply the surgical fix, and verify it passes.