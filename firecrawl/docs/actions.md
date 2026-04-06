# Browser Actions Reference

Browser actions let you interact with pages before extracting content. Pass an `actions` array in scrape requests.

## Action Types

### wait — Wait for time or element

```json
{"type": "wait", "milliseconds": 2000}
{"type": "wait", "selector": "#content-loaded"}
```
Use `milliseconds` OR `selector`, not both. Max wait: 60000ms.

### click — Click an element

```json
{"type": "click", "selector": "#submit-btn"}
{"type": "click", "selector": ".load-more", "all": true}
```
Set `all: true` to click all matching elements.

### write — Type text

```json
{"type": "write", "text": "search query"}
```
Types into the currently focused element. Usually preceded by a click on an input field.

### press — Press a key

```json
{"type": "press", "key": "Enter"}
{"type": "press", "key": "Tab"}
```
Supports standard key names: Enter, Tab, Escape, ArrowDown, etc.

### scroll — Scroll the page

```json
{"type": "scroll", "direction": "down"}
{"type": "scroll", "direction": "up"}
{"type": "scroll", "direction": "down", "selector": "#scrollable-div"}
```

### screenshot — Capture screenshot

```json
{"type": "screenshot"}
{"type": "screenshot", "fullPage": true, "quality": 80}
```
Returns base64 image in results.

### scrape — Capture current state

```json
{"type": "scrape"}
```
Captures the page content at this point in the action chain. Useful after interactions.

### executeJavascript — Run custom JS

```json
{"type": "executeJavascript", "script": "document.querySelector('.popup').remove()"}
```

### pdf — Generate PDF

```json
{"type": "pdf"}
{"type": "pdf", "landscape": true, "scale": 0.8, "format": "A4"}
```
Formats: A0-A6, Letter, Legal, Tabloid, Ledger.

## Common Patterns

### Login then scrape

```json
{
  "url": "https://app.example.com/login",
  "formats": ["markdown"],
  "actions": [
    {"type": "click", "selector": "#email"},
    {"type": "write", "text": "user@example.com"},
    {"type": "click", "selector": "#password"},
    {"type": "write", "text": "password123"},
    {"type": "click", "selector": "#login-btn"},
    {"type": "wait", "milliseconds": 3000},
    {"type": "scrape"}
  ]
}
```

### Infinite scroll page

```json
{
  "url": "https://example.com/feed",
  "formats": ["markdown"],
  "actions": [
    {"type": "scroll", "direction": "down"},
    {"type": "wait", "milliseconds": 1500},
    {"type": "scroll", "direction": "down"},
    {"type": "wait", "milliseconds": 1500},
    {"type": "scroll", "direction": "down"},
    {"type": "wait", "milliseconds": 1500},
    {"type": "scrape"}
  ]
}
```

### Dismiss popup then scrape

```json
{
  "url": "https://example.com",
  "formats": ["markdown"],
  "actions": [
    {"type": "wait", "milliseconds": 2000},
    {"type": "executeJavascript", "script": "document.querySelector('.cookie-banner')?.remove(); document.querySelector('.modal-overlay')?.remove();"},
    {"type": "scrape"}
  ]
}
```

### Search within a site

```json
{
  "url": "https://docs.example.com",
  "formats": ["markdown"],
  "actions": [
    {"type": "click", "selector": "input[type=search]"},
    {"type": "write", "text": "API reference"},
    {"type": "press", "key": "Enter"},
    {"type": "wait", "selector": ".search-results"},
    {"type": "scrape"}
  ]
}
```

## Limits

- Max 50 actions per request
- Max wait time: 60000ms per action
- Actions execute sequentially in order
