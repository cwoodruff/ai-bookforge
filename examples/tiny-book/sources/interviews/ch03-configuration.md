# Interview: Chapter 3: Configuring and Troubleshooting Brewlog

Source: interview with AI Book Forge Example, 2026-11-07. Example answers written for the demo book, standing in for a real `/interview` session.

## What value does NO_COLOR need?

Any value at all. If `NO_COLOR` is set to anything that isn't empty, Brewlog prints plain text with no colors. Setting it to an empty string does nothing.

```bash
NO_COLOR=1 brewlog list
```

## When units is imperial, what units do the options take?

You still type grams and Celsius on the command line, even with `units = "imperial"`. The setting only changes how `brewlog list` and `brewlog best` display numbers. Exports always use grams and Celsius too.
