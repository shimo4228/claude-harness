<!-- origin: shimo4228 -->

# Review output format

`editor` と `essay-reviewer` が共有する report の骨格。正本はこのファイルで、各 agent は複製しない。

```markdown
## 📊 Review Summary

**Overall Assessment:** [EXCELLENT / GOOD / NEEDS REVISION / MAJOR ISSUES]

**Strengths:**
- [List 2-3 strong points]

**Issues Found:**
- [List all issues by category]

---

## 🔴 CRITICAL Issues (Must Fix)

[Issues that must be fixed before publication]

---

## 🟡 MEDIUM Issues (Strongly Recommended)

[Issues that should be fixed for quality]

---

## 🟢 MINOR Issues (Nice to Have)

[Suggestions for improvement]

---

## 💡 Suggestions

[Additional ideas to strengthen the article]

---

## Canonical coverage

- Applied canon: [source section names]
- Not applicable: [requirement + reason]
- Pending / unverified: [まだ実行できない検査（post-fact-check recheck 等）や不足入力、なければ none]
- Must-fix violations: [CRITICAL finding references, or none]
- Advisory findings: [MEDIUM/MINOR finding references, or none]

---

## パネル所見（公開可否ではない）

[NO BLOCKERS / CRITICAL あり — 解消が必要]

> **本 agent は公開可否を出さない。**
```

受け入れの集約と公開 GO は `quality-gate` skill と著者が持つ。
