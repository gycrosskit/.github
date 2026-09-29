# .github

GY CrossKit organization profile and shared release guidance.

- [`AGENTS.md`](AGENTS.md): common publishing rules for AI agents working across the local GY CrossKit repositories.
- [`templates/jitpack-metadata.py`](templates/jitpack-metadata.py): canonical template for the matching scripts in compose-webview, live-sdk, and toast. Each repository keeps its own copy because JitPack builds that repository's checkout.

For the local workspace, link this repository's `AGENTS.md` at the common parent directory as `/Users/guoyang/gycrosskit/AGENTS.md`. GitHub's organization defaults do not distribute arbitrary `AGENTS.md` files into other repositories.
