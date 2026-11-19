# B's scientific background — 2026-11-18

External literature is not proof of any Vera-specific learning, feeling, identity or runtime.

- Huang et al., ICLR 2024, *Large Language Models Cannot Self-Correct Reasoning Yet*, https://proceedings.iclr.cc/paper_files/paper/2024/hash/8b4add8b0aa8749d80a34ca5d941c355-Abstract-Conference.html — intrinsic reasoning self-correction without external feedback may fail or degrade results.
- Kamoi et al., TACL 2024, *When Can LLMs Actually Correct Their Own Mistakes?*, https://arxiv.org/abs/2406.01297 — source-grounded external feedback matters; self-critique alone is unreliable in general settings.
- Wang et al., ICLR 2024, *MINT: Evaluating LLMs in Multi-turn Interaction with Tools and Language Feedback*, https://proceedings.iclr.cc/paper_files/paper/2024/hash/8a0d3ae989a382ce6e50312bc35bf7e1-Abstract-Conference.html — multi-turn user feedback is a distinct evaluation problem from first-answer quality.
- Maharana et al., ACL 2024, *Evaluating Very Long-Term Conversational Memory of LLM Agents*, https://aclanthology.org/2024.acl-long.747/ — LoCoMo examines temporal/long-range dialogue and identifies persistent retrieval/reasoning gaps.
- Chen et al., Findings ACL 2024, *LLMs cannot find reasoning errors, but can correct them given the error location*, https://aclanthology.org/2024.findings-acl.826/ — error detection/verification and revision must be separated.

Source-only design implication: prefer current, exactly identified external corrections and conservative applicability tests, with negative controls guarding previously good answers. No live model assessor, independent host runtime, durable parameter change or human-neurology transfer is established.
