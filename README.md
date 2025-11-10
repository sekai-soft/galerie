# Galerie

## Development

### Setup
This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Install dependencies
uv sync
```

### Running the server
```bash
uv run flask run --reload
```

### Running tests
```bash
uv run pytest -vv
```

### Translate strings
1. Put raw English strings in code using `_(...)` and `_l(...)`
2. Run `uv run flask translate update`
    * See `babel.cfg` for what files are scanned
3. Edit updated `po` files
4. Run `uv run flask translate compile` and restart server

### Migrate database schemas
`uv run flask migrate-database`
