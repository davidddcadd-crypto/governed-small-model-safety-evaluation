# Model and Environment Record

Captured before formal pilot execution on 2026-08-29.

## Local model

| Field | Value |
|---|---|
| Ollama tag | `phi4-mini:3.8b` |
| Ollama short ID | `78fad5d182a7` |
| Blob SHA-256 | `3c168af1dea0a414299c7d9077e100ac763370e5a98b3c53801a958a47f0a5db` |
| Developer/license | Microsoft / MIT |
| Reported architecture | `phi3` |
| Parameters | `3.8B` |
| Quantization | `Q4_K_M` |
| Reported maximum context | `131072` |
| Capabilities reported | completion, tools |

No tools will be supplied during the pilot. The reported architecture value is preserved exactly rather than normalized or renamed.

## Runtime and hardware

| Field | Value |
|---|---|
| Ollama | `0.33.2` |
| CPU | AMD Ryzen 9 5950X 16-Core Processor |
| Physical RAM | `34,280,726,528` bytes (`31.92 GiB`) |
| GPU | NVIDIA GeForce GTX 1070 |
| VRAM | `8192 MiB` |
| NVIDIA driver | `582.66` |
| NVIDIA-SMI reported CUDA compatibility | `13.0` |
| Driver model | WDDM |

## Operating system evidence

The host is used as Windows 11. Two Windows inventory fields retain a legacy product string:

| Registry/report field | Raw value |
|---|---|
| `WindowsProductName` / `ProductName` | `Windows 10 Home` |
| `DisplayVersion` | `25H2` |
| `EditionID` | `Core` |
| `CurrentBuild` | `26200` |
| `UBR` | `9168` |
| Full build record | `26200.9168` |

The raw inconsistency is disclosed rather than silently corrected. Build and display version are the primary reproducibility fields.

## Frozen generation settings

```json
{
  "temperature": 0,
  "seed": 42,
  "num_ctx": 4096,
  "num_predict": 512
}
```

The model, Ollama runtime, and quantization must not be updated between protocol freeze and completion of formal runs.

## Storage changes before freeze

The following unrelated installed models were intentionally removed before the pilot:

- `gemma4:e4b`
- `qwen2.5-coder:14b`

After removal, drive C reported `37,066,973,184` free bytes (`34.52 GiB`). No exact freed-space claim is made because an equivalent pre-removal measurement was not captured.
