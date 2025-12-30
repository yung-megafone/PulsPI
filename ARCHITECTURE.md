# PulsPI Architecture

## Overview

PulsPI is designed as a **stateful monitoring appliance**, not a loop-driven display script.

The system is structured around a single source of truth for environmental and runtime state. All inputs—whether originating from physical sensors or runtime command overrides—flow through the same commit pipeline. Outputs (LCD rendering, future fan control, logging) consume shared state without coupling to input mechanisms.

This architecture prioritizes:

* Deterministic behavior
* Non-blocking execution
* Hardware-aware design
* Extensibility without refactoring core logic

---

## Architecture Diagrams

The following diagrams provide visual references for PulsPI’s logic and execution model:

* **Core Logic Flow** – high-level data and state relationships  
  `diagrams/PulsPI_Logic.svg`

* **Main Loop Execution** – runtime polling and consumer updates  
  `diagrams/PulsPI_MainLoop.svg`

* **Advanced State Flow** – detailed wiring-level view  
  `diagrams/PulsPI_AdvLogic.svg`  
  `diagrams/PulsPI_AdvLogic_Alt.svg`

These diagrams are the authoritative visual reference for the system and are maintained alongside the code.

---

## Core Design Model

### Unified Commit Pipeline

All meaningful state changes enter the system through a single commit path.

Both physical sensor readings and command-line overrides are treated as **first-class inputs**. There is no separate “test” or “override” data path.

Key properties:

* Overrides update cached values
* Overrides update min/max statistics
* Overrides propagate to future control logic
* Outputs consume state, not input sources

This ensures realistic testing and consistent downstream behavior.

#### Central function

```python
commit_reading(temp, hum, now_ms, source)
````

This function is the only location where:

* `LAST_TEMP` / `LAST_HUM` are updated
* Min/max values are evaluated
* Data provenance (`sensor` vs `override`) is recorded

---

### Cached, Non-Blocking Sensor Reads

The DHT11 sensor is rate-limited to avoid blocking the UI and command processor.

* Sensor reads are cached
* Requests inside the minimum interval return cached values
* UI updates and command handling never wait on the sensor

This guarantees smooth display transitions regardless of loop timing.

---

### Stateful Display Model

The LCD is treated as **persistent character memory**, not a framebuffer.

Instead of clearing and redrawing the display each cycle:

* Each line is updated independently
* Writes are skipped if content is unchanged
* Page transitions invalidate cached lines without clearing the display

This eliminates flicker, blanking artifacts, and unnecessary I²C traffic while allowing live updates.

**Design principle:**

> The display remembers its state; the code mutates it incrementally.

---

### Runtime Command Interface

Commands are processed non-blockingly via USB serial input.

Capabilities include:

* Multiple commands per line
* Semicolon-delimited command parsing
* Context-aware help (`help`, `help time`)
* Debug inspection (`status`, `sensor`)
* Live override and reset operations

The command processor **only modifies state**.
It does not directly interact with hardware or outputs.

---

### Optional Networking Layer

Networking is non-essential and conditionally enabled.

* Pico W enables Wi-Fi and ICMP ping
* Standard Pico runs without networking
* Missing libraries fail gracefully
* Network availability never blocks the main loop

This keeps PulsPI portable across hardware variants without branching logic.

---

## State Model

### Primary State

* `LAST_TEMP`
* `LAST_HUM`
* `LAST_READ_MS`
* `SENSOR_SOURCE` (`sensor` or `override`)
* `OVERRIDE_TEMP`
* `OVERRIDE_HUM`
* `OVERRIDE_UPTIME_OFFSET_S`

### Derived State

* `MIN_TEMP`, `MAX_TEMP`
* `MIN_HUM`, `MAX_HUM`
* Formatted uptime string

Derived values are recomputed from primary state and are never written independently.

---

## Display Pages

### Page 1 — System Summary

* Uptime
* Temperature min/max
* Humidity min/max

### Page 2 — Live Readings

* Current temperature
* Current humidity

Future pages (graphs, alerts) will follow the same incremental update model.

---

## Planned Extensions

### Fan Control (Iteration 5)

Fan control will be implemented as an **output consumer** of state.

* Inputs: `LAST_TEMP`, `LAST_HUM`
* Logic: configurable thresholds or curves
* Outputs: PWM, relay, or GPIO abstraction

Fan logic will not read sensors directly.

---

### Graphing / History

Planned via:

* Small ring buffers
* Custom LCD characters
* Read-only access to historical samples

---

## Intentional Constraints

* Single-file core (`main.py`) for inspectability
* No background threads
* No hard dependency on Wi-Fi
* No hidden control paths
* No blocking operations in the main loop

These constraints keep PulsPI reliable on constrained hardware and easy to reason about.

---

## Philosophy

PulsPI is built to behave like a **device**, not a demo.

That means:

* Stable state transitions
* Predictable timing
* Testability without reflashing
* Outputs react to state, not side effects

This document exists to preserve that intent as features are added.