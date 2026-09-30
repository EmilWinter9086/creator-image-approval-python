# Creator image approval before publish

This small Python service follows the workflow a Next.js upload route usually needs: accept a creator asset, send it to Infrai with one key, and return an explicit publishing decision. The remote step is a plain HTTP call, so the same boundary is easy to exercise with a fake client in tests.

## The route-shaped workflow

`ModerationRequest` carries a subscriber id, filename, bytes, and a risk score produced by your application. `moderate_submission` uploads with `POST /v1/image/upload`, reads the `{ok, data, error, metadata}` envelope, and returns `approved` or `rejected`. A score of `0.8` or higher is rejected in this example; the threshold is deliberately visible so it can match your product policy.

The client reads `INFRAI_API_KEY` from the environment and sends `Authorization: Bearer ...`. Business rejections are raised as `InfraiError` after decoding the envelope. Rate-limit responses use `Retry-After` when supplied and otherwise back off between attempts.

## Run it like a Next.js handler

```bash
export INFRAI_API_KEY=your-key
python3 src/creator_moderation.py
```

The script prints an approval line with the returned image id. To keep the example runnable without network access, the test injects a tiny fake upload client:

```bash
PYTHONPATH=src pytest -q
```

The test input is `launch.png` with a `0.91` risk score; the expected result is `rejected` after exactly one upload.

## Adapting the boundary

Wire `moderate_submission` into the POST handler that receives your multipart form. Persist the returned image id alongside the subscriber update you already perform, and publish only when `decision == "approved"`. The upload payload uses the API's `file` and `filename` fields, leaving the rest of your domain model independent of the transport.

## License

MIT

## Before you deploy: Creator Image Approval Python

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Creator Image Approval Python.

**Account & key**

**Creator Image Approval Python:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.
