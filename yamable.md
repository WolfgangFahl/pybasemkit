# yamable — YamlAble & lod_storable

Module: `basemkit/yamlable.py`

Provides YAML and JSON serialization/deserialization for Python dataclasses via
the `YamlAble` base class and the `@lod_storable` decorator.

---

## Overview

`YamlAble` is a generic mixin that adds YAML and JSON I/O to any `@dataclass`.
It handles:

- Serializing to YAML with block-scalar strings and optional omission of `None`
  values and underscore-prefixed attributes
- Deserializing from YAML strings, streams, files, and URLs
- Serializing to / deserializing from JSON (delegating to `dataclasses-json`)
- Recursive filtering of `None`, empty collections, and private attributes
  before serialization

The `@lod_storable` decorator is a one-shot convenience that applies
`@dataclass`, `@dataclass_json`, **and** `YamlAble` inheritance to a plain
class with a single annotation.

---

## Quick Start

### Using `@lod_storable` (recommended)

```python
from typing import Optional
from basemkit.yamlable import lod_storable

@lod_storable
class Person:
    name: str
    age: int
    email: Optional[str] = None

# Serialize
p = Person(name="Alice", age=30)
print(p.to_yaml())
# name: Alice
# age: 30

# Deserialize
p2 = Person.from_yaml("name: Bob\nage: 25\n")
print(p2.name)  # Bob
```

### Using `YamlAble` directly

When you need explicit control over the MRO or already have `@dataclass` and
`@dataclass_json` applied:

```python
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from basemkit.yamlable import YamlAble

@dataclass_json
@dataclass
class Config(YamlAble):
    host: str = "localhost"
    port: int = 8080
```

---

## `@lod_storable` Decorator

```python
def lod_storable(cls):
```

Transforms a plain class into a fully capable storable dataclass by:

1. Applying `@dataclass` — adds `__init__`, `__repr__`, `__eq__`, etc.
2. Applying `@dataclass_json` — adds `from_json` / `to_json` / `from_dict` /
   `to_dict`
3. Creating an inner `LoDStorable` class that inherits from both `YamlAble`
   and the decorated class, then restoring `__name__`, `__doc__`, and
   `__module__` so the class identity is transparent to serializers and
   module lookups.

The name *LoDStorable* stands for **List-of-Dicts Storable** — the pattern
used throughout pyLoDStorage for tabular in-memory data.

---

## `YamlAble` Class

```python
class YamlAble(Generic[T]):
```

### YAML Serialization

#### `to_yaml`

```python
def to_yaml(
    self,
    ignore_none: bool = True,
    ignore_underscore: bool = True,
    allow_unicode: bool = True,
    sort_keys: bool = False,
) -> str:
```

Converts the dataclass instance to a YAML string.

| Parameter | Default | Effect |
|---|---|---|
| `ignore_none` | `True` | Omit keys whose value is `None` |
| `ignore_underscore` | `True` | Omit keys whose name starts with `_` |
| `allow_unicode` | `True` | Emit unicode characters unescaped |
| `sort_keys` | `False` | Alphabetically sort mapping keys |

Multi-line strings are automatically rendered in **block scalar style** (`|`),
preserving newlines readably.

```python
obj.to_yaml()
# description: |-
#   First line
#   Second line
# name: Example
```

#### `save_to_yaml_stream` / `save_to_yaml_file`

```python
def save_to_yaml_stream(self, file: TextIO) -> None:
def save_to_yaml_file(self, filename: str) -> None:
```

Write YAML output to an open stream or a file path (UTF-8).

```python
obj.save_to_yaml_file("/tmp/config.yaml")
```

---

### YAML Deserialization

All three class methods return a fully constructed instance of the calling
class (`cls`).

#### `from_yaml`

```python
@classmethod
def from_yaml(cls: Type[T], yaml_str: str) -> T:
```

Parses a YAML string and reconstructs the dataclass via `dacite.from_dict`.
Handles `null` values in YAML correctly for `Optional` fields.

```python
instance = MyClass.from_yaml(yaml_string)
```

#### `load_from_yaml_stream`

```python
@classmethod
def load_from_yaml_stream(cls: Type[T], stream: TextIO) -> T:
```

Reads the entire stream and delegates to `from_yaml`.

#### `load_from_yaml_file`

```python
@classmethod
def load_from_yaml_file(cls: Type[T], filename: str) -> T:
```

Opens `filename` in text mode and delegates to `load_from_yaml_stream`.

```python
config = Config.load_from_yaml_file("config.yaml")
```

#### `load_from_yaml_url`

```python
@classmethod
def load_from_yaml_url(cls: Type[T], url: str) -> T:
```

Fetches the URL with `urllib.request` and delegates to `from_yaml`.
Raises `Exception` if the HTTP status is not 200.

---

### JSON Serialization / Deserialization

JSON support is provided by `dataclasses-json` and is available on any class
decorated with `@lod_storable` (or `@dataclass_json` directly). `YamlAble`
adds file and URL convenience wrappers.

#### `save_to_json_file`

```python
def save_to_json_file(self, filename: str, **kwargs: Any) -> None:
```

Serializes to JSON and writes to `filename` (UTF-8). Extra `**kwargs` are
forwarded to `to_json()`.

#### `load_from_json_file`

```python
@classmethod
def load_from_json_file(cls: Type[T], filename: Union[str, Path]) -> T:
```

Reads a JSON file and reconstructs the instance via `from_json`.

#### `load_from_json_url`

```python
@classmethod
def load_from_json_url(cls: Type[T], url: str) -> T:
```

Fetches JSON from a URL and reconstructs the instance.

---

### Filtering Helper

#### `remove_ignored_values`

```python
@classmethod
def remove_ignored_values(
    cls,
    value: Any,
    ignore_none: bool = True,
    ignore_underscore: bool = False,
    ignore_empty: bool = True,
) -> Any:
```

Recursively walks a dict / list structure and removes entries that match the
active ignore flags. Called internally by `to_yaml` but also usable standalone.

| Flag | Default | Removes |
|---|---|---|
| `ignore_none` | `True` | Keys with `None` values |
| `ignore_underscore` | `False` | Keys whose name starts with `_` |
| `ignore_empty` | `True` | Empty dicts, lists, sets, tuples |

Strings and bytes are treated as scalars, not iterables, and are never
removed by `ignore_empty`.

---

### `from_dict2`

```python
@classmethod
def from_dict2(cls: Type[T], data: dict) -> T:
```

Alternative deserializer using `dacite.from_dict` instead of
`dataclasses-json`. Returns `None` if `data` is falsy. Useful when
`dataclasses-json` is not available or when `dacite`'s strict type coercion
is preferred.

---

## `DateConvert` Helper

```python
class DateConvert:
    @classmethod
    def iso_date_to_datetime(cls, iso_date: str) -> date:
```

Converts an ISO 8601 date string (`"YYYY-MM-DD"`) to a `datetime.date`
object. Returns `None` if `iso_date` is falsy. Intended as a `dacite`
type-hook for fields typed as `date`.

---

## Internal Representers

These are set up automatically by `_yaml_setup()` on the first call to
`to_yaml()` and should not need to be called directly.

| Method | Purpose |
|---|---|
| `represent_none` | Renders `None` as an empty YAML scalar (`""`) rather than `null` |
| `represent_literal` | Renders strings containing `\n` in block scalar style (`\|`) |

---

## Dependencies

| Package | Role |
|---|---|
| `PyYAML` | YAML parsing and emission |
| `dacite` | Strict dict-to-dataclass construction (`from_dict2`) |
| `dataclasses-json` | JSON serialization (`from_json`, `to_json`, `from_dict`) |

---

## Notes

- `YamlAble` requires the instance to be a dataclass (`is_dataclass(self)` is
  asserted in `_yaml_setup`). A `ValueError` is raised otherwise.
- The YAML dumper is cached on `self._yaml_dumper` after the first setup call;
  custom representers are registered only once per instance.
- URL loading uses the stdlib `urllib.request` — no `requests` dependency.
- `lod_storable` preserves `__name__`, `__qualname__`, `__doc__`, and
  `__module__` so `pickle`, `dacite`, and `dataclasses-json` can resolve the
  class correctly.
