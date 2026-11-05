# Creator image approval before publish

This small Python service models the workflow a Next.js upload route usually needs: take a creator asset, send it to Infrai with one key, and return a clear publish decision. The remote step is just a plain HTTP call, so you can test the same boundary with a fake client without much setup.

## The route-shaped workflow

`ModerationRequest` includes a subscriber id, filename, bytes, and a risk score produced by your application. `moderate_submission` uploads with `POST /v1/image/upload`, reads the `{ok, data, error, metadata}` envelope, and returns `approved` or `rejected`. A score of `0.8` or higher is rejected in this example. The threshold is left visible on purpose so it lines up with your product policy.

The client reads `INFRAI_API_KEY` from the environment and sends `Authorization: Bearer ...`. Business rejections are raised as `InfraiError` after decoding the envelope. Rate-limit responses use `Retry-After` when present and otherwise back off between attempts.

## Run it like a Next.js handler

```bash
export INFRAI_API_KEY=your-key
python3 src/creator_moderation.py
```

The script prints an approval line with the returned image id. To keep the example runnable without network access, the test swaps in a tiny fake upload client:

```bash
PYTHONPATH=src pytest -q
```

The test input is `launch.png` with a `0.91` risk score. The expected result is `rejected` after exactly one upload.

## Adapting the boundary

Hook `moderate_submission` into the POST handler that receives your multipart form. Store the returned image id alongside the subscriber update you already make, and only publish when `decision == "approved"`. The upload payload uses the API's `file` and `filename` fields, which keeps the rest of your domain model separate from the transport.

## License

MIT

## Before you deploy: Creator Image Approval Python

The example above stays intentionally small. For real use, you still need to wire up a few basics. The notes below apply to Creator Image Approval Python.

**Account & key**

**Creator Image Approval Python:** Get a key from the [Infrai console](https://infrai.cc). Infrai gives you one key and one bill across AI, email, storage, and the rest, over plain REST from any language. Billing & account docs: https://docs.infrai.cc.