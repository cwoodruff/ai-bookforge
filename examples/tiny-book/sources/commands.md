# Brewlog Commands

All commands accept `--journal PATH` to use a journal folder other than `~/.brewlog/`.

## brewlog bean add

```bash
brewlog bean add "Ethiopia Guji" --roaster "Northside" --roasted 2026-10-28
```

Registers a bean. The name must be unique. `--roasted` takes a date in `YYYY-MM-DD` form and is optional.

## brewlog add

```bash
brewlog add --method v60 --bean "Ethiopia Guji" --dose 15 --water 250 --grind 22 --temp 94 --time 3:10 --rating 4
```

| Option | Meaning | Default |
|---|---|---|
| `--method` | Brew method | `default_method` from config |
| `--bean` | A registered bean name | required |
| `--dose` | Coffee in grams | required |
| `--water` | Water in grams | `dose * default_ratio` |
| `--grind` | Grinder setting, any number | none |
| `--temp` | Water temperature in Celsius | `default_temp` from config |
| `--time` | Brew time as `M:SS` | none |
| `--rating` | 1 to 5 | none |
| `--note` | Free text | none |

Brewlog rejects a rating outside 1 to 5, a dose of zero or less, and an unknown bean name (exit code 2).

## brewlog list

```bash
brewlog list --bean "Ethiopia Guji" --method v60 --last 10
```

Prints a table of brews, newest first. `--last N` limits the count (default 20). `--min-rating N` hides brews rated below N.

## brewlog edit

```bash
brewlog edit 42 --rating 5 --note "sweeter after resting the beans"
```

Appends a new revision of brew 42 with the changed fields.

## brewlog best

```bash
brewlog best --bean "Ethiopia Guji"
```

Shows the highest-rated brew for each method used with that bean. Ties go to the most recent brew.

## brewlog export

```bash
brewlog export --format csv > brews.csv
```

Formats: `csv` and `json`. Export always writes the latest revision of each brew.
