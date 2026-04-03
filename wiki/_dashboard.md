# Knowledge Base Dashboard

## Recent Articles
```dataview
TABLE title, status, updated
FROM "wiki/concepts"
SORT updated DESC
LIMIT 20
```

## Draft Articles (need review)
```dataview
LIST
FROM "wiki/concepts"
WHERE status = "draft"
SORT created DESC
```

## Tag Cloud
```dataview
TABLE WITHOUT ID
  length(rows) AS "Count",
  rows.file.link AS "Articles"
FROM "wiki/concepts"
FLATTEN tags AS tag
GROUP BY tag
SORT length(rows) DESC
```

## Stub Articles (need content)
```dataview
LIST
FROM "wiki/concepts"
WHERE status = "stub"
```
