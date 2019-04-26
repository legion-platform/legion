# Feedback subsystem

**NOTE: Described below requires `feedback` to be enabled in the HELM's chart configuration during deploy.**

Feedback system is described in a [special section](./gs_feedback_loop.md).

Usage of feedback system with examples [placed here](./ref_feedback_loop_protocol.md).

Implementation details:
* FluentD log aggregator - gathers logs from EDI and feedback aggregator instances using FluentD forwarding protocol.
* Feedback aggregator - provides HTTP endpoint for aggregating feedback.