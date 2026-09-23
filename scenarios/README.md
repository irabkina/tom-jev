# Scenarios

One scenario per file, named `<id>.yaml` or `<id>.yml`, matching
`tom_jev.models.Scenario`:

```yaml
id: example-01
text: The narrative, as a participant would read it.

entities:
  - id: a
    name: Ana
  - id: b
    name: Ben

relations:
  - source: a
    target: b
    kind: tells
```

`attributes` is optional on both entities and relations — omit it when
empty, or use it to carry whatever the scenario needs:

```yaml
entities:
  - id: a
    name: Ana
    attributes:
      role: speaker

relations:
  - source: a
    target: b
    kind: tells
    attributes:
      when: before-ben-leaves
```

Long narratives read better as a block scalar, which preserves newlines:

```yaml
text: |
  Ana puts the key under the mat while Ben watches.
  After Ben leaves the room, Ana moves the key into the drawer.
```

`text` carries the rich representation; `entities` and `relations` carry the
sparse one. Both describe the same scenario — keep them in sync.
