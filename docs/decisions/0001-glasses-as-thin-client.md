# 0001. Glasses are a thin client

Status: accepted

## Context

Current XR glasses have a few watts of power budget, tight thermal limits and short battery life. Vendors and SDKs are also changing quickly (Android XR, Snap OS, Meta, visionOS). Anything built deeply into one headset is likely to need rewriting.

## Decision

The glasses only render primitives in world coordinates and report head pose, gaze and speech. Map building, belief filtering, intent resolution and planning all run in the brain layer on a laptop or phone, or on the robot itself.

## Consequences

- Most of the system can be built and tested with a desktop viewer before any glasses are involved.
- Moving to a different headset means rewriting one client, not the system.
- The link between the brain and the glasses becomes latency-sensitive. Rendering has to tolerate late or missing updates.
