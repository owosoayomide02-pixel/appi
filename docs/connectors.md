# Connectors

Action selection order:

```
1. Official API connector
2. OS-native integration
3. Browser automation
4. Desktop/mobile UI automation
5. Ask the user
```

Do not use UI automation when a safer authenticated API exists.

## Catalog (none of these are silently “connected”)

## GitHub (first real connector)

GitHub can be connected in three ways. None mark **Connected** until `GET https://api.github.com/user` succeeds.

1. **OAuth authorization code** — requires `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET`
2. **OAuth device flow** — requires `GITHUB_CLIENT_ID` (user enters a code at github.com/login/device)
3. **Verified personal access token** — paste a PAT on Connections; Appi calls GitHub before storing it in the vault

Reads: `github.user`, `github.repos`. Guardian still runs. No token is sent to the model.

## Gmail (cloud connector)

Gmail can be connected in two ways. None mark **Connected** until `GET https://gmail.googleapis.com/gmail/v1/users/me/profile` returns `emailAddress`.

1. **OAuth authorization code** — requires `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`. Redirect: `http://127.0.0.1:8000/api/v1/connections/gmail/oauth/callback`
2. **Verified Google access token** — paste a token on Connections; Appi calls Gmail profile before storing it in the vault

Tools: `gmail.profile`, `email.read`, `email.search` (ALLOW when connected), `email.draft` (ASK), `email.send` (ASK, high). Cloud-side only — not dispatched to the device. No token is sent to the model. Send is never faked.

Connecting Gmail does **not** connect Calendar or Contacts. Those stay `not_connected` until their own OAuth scopes exist.

## Google Calendar (cloud connector)

Google Calendar is a separate connector from Gmail. None mark **Connected** until `GET https://www.googleapis.com/calendar/v3/users/me/calendarList` succeeds.

1. **OAuth authorization code** — same `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`. Redirect: `http://127.0.0.1:8000/api/v1/connections/google_calendar/oauth/callback`
2. **Verified Google access token** — paste a token with Calendar scopes; Appi calls calendarList before storing it

Tools: `calendar.read` (ALLOW when connected), `calendar.write` / `calendar.create` (ASK). Cloud-side only. Creating an event is never faked: missing title or start time fails instead of inventing one.

Connecting Calendar does **not** connect Gmail or Contacts.

Later: social, communication, payments, financial integrations.

Supabase remains a stored-secret ping, not a general cloud operator.

## Payments

`payment.prepare` / `payment.execute` / `transfer.execute` stay behind Guardian.

No approved Paystack/Stripe/open-banking connection → `CONNECTOR_NOT_CONNECTED`. Appi does not pretend a transfer happened.

Card numbers and bank passwords are never stored.
