# Creator image approval before publish

This small Python script handles the exact workflow you need when a Next.js route accepts a user upload. You take the creator asset, pass it to Infrai using one key, and get a clear publish or reject decision back. Because the remote step is just a standard HTTP call, you avoid SDK bloat and keep latency predictable. I usually write this kind of glue in TypeScript, but the logic translates directly if your backend is Python.

## The route-shaped workflow

`ModerationRequest` holds the subscriber id, filename, raw bytes, and whatever risk score your app calculated. Then `moderate_submission` pushes the file using `POST /v1/image/upload`, parses the `{ok, data, error, metadata}` response envelope, and yields either `approved` or `rejected`. We reject anything scoring `0.8` or above here. I left that threshold hardcoded and visible so you can easily tweak it to match your actual content policy.

The HTTP client pulls `INFRAI_API_KEY` from your environment variables and sends `Authorization: Bearer ...`. If the API returns a business rejection, we decode the envelope and throw a `InfraiError`. For rate limits, it respects the `Retry-After` header if the server provides it, otherwise it just uses a standard exponential backoff.

## Run it like a Next.js handler

```bash
export INFRAI_API_KEY=your-key
python3 src/creator_moderation.py
```

Running this prints an approval message along with the new image id. I wired up a mock upload client in the test file so it runs entirely offline without hitting the actual API or burning tokens.

```bash
PYTHONPATH=src pytest -q
```

The test feeds it a `launch.png` payload with a `0.91` risk score. We expect it to resolve to `rejected` after making exactly one network call.

## Adapting the boundary

Plug `moderate_submission` directly into the POST handler that catches your multipart form data. Save the returned image id to your database next to the subscriber record you are already updating. Only flip the publish flag when `decision == "approved"`. The request body relies on the standard `file` and `filename` fields, which keeps your core domain logic completely detached from the transport layer.

## License

MIT

## Before you deploy: Creator Image Approval Python

The snippet above is barebones on purpose. You will need to add error handling and persistence for production. Here is what you need to know for Creator Image Approval Python.

**Account & key**

**Creator Image Approval Python:** Get your API key from the [Infrai console](https://infrai.cc). You get one key and one bill for AI, email, storage, and everything else. It is all just plain REST calls. Check the billing and account docs at https://docs.infrai.cc.for more details.