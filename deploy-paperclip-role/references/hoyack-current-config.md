# Hoyack Paperclip Role Deployment Reference

Do not store secrets in this file.

## Hosts

- Leonidas K3s context: `leonidas-k3s`
- Paperclip namespace: `paperclip`
- Paperclip deployment: `paperclip`
- Public URL: `https://paperclip.hoyack.ai`
- Health URL with Cloudflare resolve override: `curl --resolve paperclip.hoyack.ai:443:104.18.35.222 https://paperclip.hoyack.ai/api/health`

## SSH

- `ssh leonidas` reaches the x86 K3s node and OpenClaw gateway host.
- `ssh spartacus` reaches the ARM OpenClaw host.

## Current Paperclip IDs

- Company: `0a97037e-27d6-4f0a-a546-b727063169da`
- CEO: `51a10671-fbd5-4e84-bda4-549b28968742`, adapter `hermes_local`
- COO: `c05ed82d-2dd0-4392-915e-3b7624f534ee`, adapter `openclaw_gateway`, OpenClaw profile `andromeda-coo`

## Current Compatibility Notes

The deployed image after COO setup was `docker.io/library/paperclip:20260705-0818`.

The OpenClaw gateway adapter was patched for Leonidas OpenClaw 2026.6.11:

- Protocol version `4`
- Device auth payload prefix `v2`
- No extra top-level `paperclip` property in `agent` requests
- Explicit scopes `operator.admin`, `operator.read`, `operator.write`
- Persistent `devicePrivateKeyPem` in adapter config

The Hermes adapter path was patched so Hermes runs unattended with `--yolo`, receives Paperclip auth through `PAPERCLIP_API_KEY = ctx.authToken`, and includes bearer auth in Paperclip curl instructions.

## Verification Examples

COO verification run `528f6590-410c-425f-9bd3-891d6e8e4ecc` succeeded with no error. It authenticated as COO, queried assigned active issues, got an empty array, and exited `status=ok`.

CEO verification run `e4f7f356-d655-4918-934d-bf449c8eaa0b` succeeded with no error using Hermes session `20260705_124031_a8adee`.
