# n8n integration and test status

The API sends these server-side events:

- `ai_summary_requested` → `N8N_AI_WEBHOOK`
- `application_received` → `N8N_EMAIL_WEBHOOK`
- `interview_scheduled` → `N8N_EMAIL_WEBHOOK`
- `decision` with `Hired` or `Rejected` → `N8N_EMAIL_WEBHOOK`

The browser never calls n8n and no AI key is exposed to the frontend. Webhook failures do not undo a saved application.

## Important for the supplied URLs

The supplied URLs use `/webhook-test/`. In n8n, open each workflow and click **Execute workflow** before submitting the website event. A test webhook returns 404 when the workflow is not listening. For an always-on deployment, activate the workflow and replace the URLs with the production `/webhook/...` URLs in `.env`.

## Synthetic test result

Both URLs were reachable, but both returned HTTP 404 with n8n's message that the webhook is not registered and the workflow must be executed first. The local application event still returned HTTP 200 and did not fail when n8n was unavailable.
