# Scenarios

One scenario per file, named `<id>.json`, matching
`jev_rerepresentation.models.Scenario`:

```json
{
  "id": "example-01",
  "text": "The narrative, as a participant would read it.",
  "entities": [
    { "id": "a", "name": "Ana", "attributes": {} },
    { "id": "b", "name": "Ben", "attributes": {} }
  ],
  "relations": [
    { "source": "a", "target": "b", "kind": "tells", "attributes": {} }
  ]
}
```

`text` carries the rich representation; `entities` and `relations` carry the
sparse one. Both describe the same scenario — keep them in sync.
