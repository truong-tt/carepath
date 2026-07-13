# Overview

## Current Behavior

Interpreter maintenance paths used a direct admin-token comparison, startup-only
retention purge, and hard-coded browser origins.

## Target Behavior

The same safe startup/lifecycle runs standalone and combined, admin checks are
constant-time, daily retention purging is cancellable, and CORS is configured
through settings.

## Non-Goals

- Change routes, risk classification, providers, or model defaults.
