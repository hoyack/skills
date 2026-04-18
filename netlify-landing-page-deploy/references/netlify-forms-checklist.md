# Netlify Forms Validation Checklist

Reference for Phase 2 of the `netlify-landing-page-deploy` pipeline. Use this to validate and auto-fix `<form>` elements before deploy.

## How Netlify Forms Work (Mental Model)

At deploy time, Netlify's build bots parse your static HTML looking for `<form>` tags marked with `data-netlify="true"` (or a bare `netlify` attribute). For each discovered form, Netlify:

1. Registers the form name (from the `name` attribute) under the site
2. Injects a hidden `form-name` field and a POST endpoint at `/` on your site
3. Captures submissions into the Netlify dashboard → Forms section

Key consequences:
- **Forms not present in static HTML at deploy time are invisible.** JS-rendered forms need a static mirror.
- **Input `name` attributes define the captured field keys.** Missing names = lost data.
- **Submissions must be URL-encoded (`application/x-www-form-urlencoded`) or `multipart/form-data`.** JSON bodies are rejected.
- **Each form name must be unique per site.** Reusing names collides submissions.

## Required Form Attributes

Every contact/lead form must have:

```html
<form name="contact" method="POST" data-netlify="true" netlify-honeypot="bot-field">
  <!-- fields -->
</form>
```

| Attribute | Required | Purpose |
|---|---|---|
| `name="<unique>"` | Yes | Identifies the form in the Netlify dashboard |
| `method="POST"` | Yes | Netlify only accepts POST |
| `data-netlify="true"` | Yes | Tells Netlify's parser to register this form |
| `netlify-honeypot="bot-field"` | Recommended | Enables honeypot spam filter |
| `action="/thank-you"` | Recommended | Redirect target after successful submit |

## Required Input Attributes

Every `<input>`, `<textarea>`, and `<select>` inside the form must have a `name` attribute:

```html
<input type="text" name="full_name" required />
<input type="email" name="email" required />
<textarea name="message" required></textarea>
```

**Auto-fix rule:** If an input has no `name`, derive one from (in order): `id`, label text, `placeholder`, `type` + index. Normalize to snake_case.

## Honeypot Pattern

Add this inside the form, hidden via CSS:

```html
<p class="hidden">
  <label>Don't fill this out if you're human: <input name="bot-field" /></label>
</p>
```

```css
.hidden { display: none; }
```

Submissions where `bot-field` is non-empty are silently discarded by Netlify.

## Success Page Pattern

Either use the default "Thank you" page Netlify generates, or supply your own via `action`:

```html
<form ... action="/thank-you">
```

And create `thank-you.html` at the site root:

```html
<!DOCTYPE html>
<html>
<head><title>Thanks!</title><meta name="viewport" content="width=device-width, initial-scale=1" /></head>
<body>
  <h1>Thanks — we got your message.</h1>
  <p><a href="/">← Back to home</a></p>
</body>
</html>
```

## JS-Rendered Form Pattern (React / Vue / SPA)

Netlify's parser only sees static HTML. For SPA forms, add a **hidden static mirror** to the root HTML file so Netlify registers the form:

```html
<!-- In public/index.html, outside the SPA mount point -->
<form name="contact" data-netlify="true" netlify-honeypot="bot-field" hidden>
  <input type="text" name="full_name" />
  <input type="email" name="email" />
  <textarea name="message"></textarea>
</form>
```

Then, in the real JS-rendered form, include a hidden `form-name` input matching the static mirror's name:

```jsx
<form name="contact" method="POST" data-netlify="true" onSubmit={handleSubmit}>
  <input type="hidden" name="form-name" value="contact" />
  <input type="text" name="full_name" />
  ...
</form>
```

## AJAX / fetch Submission

Must be URL-encoded, not JSON:

```js
const encode = (data) =>
  Object.keys(data)
    .map((k) => encodeURIComponent(k) + "=" + encodeURIComponent(data[k]))
    .join("&");

fetch("/", {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: encode({ "form-name": "contact", ...formState })
});
```

Or with `FormData`:

```js
const body = new URLSearchParams(new FormData(formEl)).toString();
fetch("/", {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body
});
```

**Do NOT** set `Content-Type: application/json` or pass `JSON.stringify(...)`. Netlify Forms will reject the submission.

## File Uploads

For forms with `<input type="file">`:

```html
<form name="job-application" method="POST" enctype="multipart/form-data" data-netlify="true">
  <input type="file" name="resume" />
</form>
```

- Use `enctype="multipart/form-data"` on the form tag
- For AJAX, submit `FormData` directly (no `Content-Type` header — let the browser set it with the boundary)
- File size limit: 8MB per file on free tier

## Validation Checklist (use during Phase 2)

For each `<form>` in the site, check:

- [ ] `name` attribute present and unique
- [ ] `method="POST"` present
- [ ] `data-netlify="true"` present
- [ ] `netlify-honeypot="bot-field"` present (or honeypot intentionally omitted)
- [ ] Honeypot input `<input name="bot-field" />` present if honeypot attribute set
- [ ] Every `<input>`, `<textarea>`, `<select>` has a `name` attribute
- [ ] No `type="submit"` input is `disabled` by default without a clear re-enable path
- [ ] If AJAX: body is URL-encoded with hidden `form-name` field
- [ ] If SPA-rendered: static mirror form exists in root HTML
- [ ] Success page exists at `action` target, or default is acceptable

## Escalation: Netlify Functions Form Handler

If a form cannot be validated statically (e.g., deeply dynamic, requires custom server-side logic like captcha verification or third-party forwarding), use a Netlify serverless function instead.

`netlify/functions/contact.js`:

```js
exports.handler = async (event) => {
  if (event.httpMethod !== "POST") {
    return { statusCode: 405, body: "Method Not Allowed" };
  }

  const params = new URLSearchParams(event.body);
  const data = Object.fromEntries(params);

  // Honeypot
  if (data["bot-field"]) {
    return { statusCode: 200, body: "OK" };
  }

  // TODO: forward to email service, CRM webhook, etc.
  // await fetch(process.env.WEBHOOK_URL, { method: "POST", body: JSON.stringify(data) });

  return {
    statusCode: 302,
    headers: { Location: "/thank-you" },
    body: ""
  };
};
```

Point the form's `action` to the function:

```html
<form name="contact" method="POST" action="/.netlify/functions/contact">
  ...
</form>
```

Note: this path bypasses Netlify's built-in Forms dashboard. Submissions will NOT appear there — the function must persist them itself (via webhook, email, DB, etc.). Set the webhook URL as an env var in Phase 5.

## Common Pitfalls

| Symptom | Likely Cause |
|---|---|
| Form submits but nothing in Netlify dashboard | Missing `data-netlify="true"`, or form is JS-rendered without static mirror |
| Submission returns 404 | `form-name` hidden input missing, or form name doesn't match a registered form |
| Submission returns 400 | `Content-Type: application/json` used instead of URL-encoded |
| Some fields captured, others missing | Inputs without `name` attributes |
| Tons of spam submissions | Honeypot not configured; consider adding reCAPTCHA via `data-netlify-recaptcha="true"` |
| Form detection fails on first deploy | Netlify parses only the live HTML — ensure it's in the deployed `publish` directory, not just source |
