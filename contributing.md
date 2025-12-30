# Contributing to PulsPI

Thanks for your interest in contributing to PulsPI.

This project prioritizes **clarity, determinism, and hardware-aware design** over rapid feature churn. Contributions are welcome, but changes should respect the architectural intent outlined in `ARCHITECTURE.md`.

If you're unsure whether a change fits, open an issue or start a discussion first.

---

## Guiding Principles

When contributing to PulsPI, keep the following principles in mind:

* **State-first design**  
  All inputs must flow through the unified commit pipeline. Outputs consume state; they do not read sensors or overrides directly.

* **Non-blocking behavior**  
  No feature should introduce blocking delays into the main loop.

* **Hardware realism**  
  PulsPI runs on constrained hardware. Avoid unnecessary abstraction, allocation, or background complexity.

* **Inspectability**  
  The core system is intentionally kept in a single file (`main.py`). Changes should not obscure control flow or state transitions.

---

## What Makes a Good Contribution

Good contributions typically include:

* Bug fixes that improve stability or correctness
* Improvements to display behavior or clarity
* Enhancements to the runtime command interface
* New output consumers (e.g., fan control, alerts) that consume existing state
* Documentation improvements (README, ARCHITECTURE, diagrams)

Changes that align with planned iterations (see README) are especially welcome.

---

## What to Avoid

Please avoid:

* Bypassing `commit_reading()` for state updates
* Direct hardware access from command handlers
* Blocking calls (`sleep`, long I/O) in the main loop
* Splitting core logic across many files without strong justification
* Introducing hard dependencies on Wi-Fi or optional peripherals

These patterns make the system harder to reason about and test.

---

## Code Style

* Keep code **explicit rather than clever**
* Prefer clear variable names over compact expressions
* Avoid magic numbers; document constraints
* Inline comments should explain *why*, not *what*

Formatting does not need to be perfect, but consistency matters.

---

## Testing Changes

Before submitting a change:

* Verify the program runs on:
  * Pico W (with and without Wi-Fi)
  * Standard Pico (no networking)
* Ensure display transitions remain flicker-free
* Test command overrides and reset paths
* Confirm no new blocking behavior was introduced

If your change adds new commands, update the help output accordingly.

---

## Documentation Changes

If you modify system behavior or data flow:

* Update `ARCHITECTURE.md`
* Update or add diagrams under `diagrams/`
* Keep diagram sources alongside exported SVGs

Documentation should reflect the code, not intentions.

---

## Submitting a Contribution

1. Fork the repository
2. Create a feature branch with a descriptive name
3. Make focused, atomic commits
4. Include clear commit messages

Example commit messages:

```

feat: add min/max reset command
fix: prevent LCD flicker during page transitions
docs: update architecture diagrams for state pipeline

```

5. Open a pull request with a brief explanation of:
   * What changed
   * Why it was necessary
   * Any trade-offs introduced

---

## Final Note

PulsPI is meant to feel like a **small, reliable device**, not a framework.

If your contribution makes the system easier to understand, easier to test, or more predictable under real hardware constraints, it's probably a good fit.

Thanks for contributing.
