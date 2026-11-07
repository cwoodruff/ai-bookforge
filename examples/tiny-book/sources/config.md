# Brewlog Configuration

Brewlog reads `config.toml` from the journal folder. Every key is optional.

```toml
default_method = "v60"
default_ratio = 16
default_temp = 93
units = "metric"
rating_scale = 5
```

| Key | Meaning | Default |
|---|---|---|
| `default_method` | Method used when `--method` is omitted | `"v60"` |
| `default_ratio` | Water-to-coffee ratio used when `--water` is omitted | `16` |
| `default_temp` | Water temperature in Celsius when `--temp` is omitted | `93` |
| `units` | `metric` or `imperial`; imperial shows ounces and Fahrenheit but still stores grams and Celsius | `"metric"` |
| `rating_scale` | Fixed at 5 in this version; other values are rejected | `5` |

## Environment variables

- `BREWLOG_JOURNAL` overrides the journal folder, the same as `--journal`. The command-line option wins if both are set.
- `NO_COLOR` turns off colored output.

## Precedence

For every setting, Brewlog uses the first value it finds in this order: the command-line option, the environment variable (where one exists), `config.toml`, and finally the built-in default.

## Troubleshooting

- "unknown bean": register it first with `brewlog bean add`. Bean names are case-sensitive.
- "invalid config key": Brewlog stops on any key it doesn't recognize, so check for typos.
- A corrupt line in `journal.jsonl` is skipped with a warning that names the line number; the rest of the journal still loads.
