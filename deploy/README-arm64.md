# PCRCalculator Linux ARM64 server

## Build

Use .NET 8 SDK and Python 3 on Linux ARM64 or cross-publish from another host.

```bash
python3 scripts/test_build_server.py
./build.sh --target linux-arm64
file Builds/LinuxARM64/publish/PCRCalculatorServer
```

The build creates `Builds/mzq-linux-arm64.zip` separately from the existing x64 package.

## Docker (ARM64)

```bash
docker build --platform linux/arm64 -f Dockerfile.arm64 -t pcrcalculator:arm64 .
docker volume create pcrcalculator-data
docker run --rm --platform linux/arm64 -p 127.0.0.1:8080:8080 \
  -v pcrcalculator-data:/data pcrcalculator:arm64
```

The server listens on port 8080 and may acquire game data at first launch. Never expose its unauthenticated HTTP API directly to the public Internet. Use a secured reverse proxy or private network.

## systemd

Copy the ARM64 publish directory to `/opt/pcrcalculator`, create a non-login `pcrcalculator` system user, and make application files readable/executable by that user. Install `deploy/pcrcalculator-arm64.service` to `/etc/systemd/system/` and run:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now pcrcalculator-arm64
sudo journalctl -u pcrcalculator-arm64 -f
```

The service listens on localhost and uses `StateDirectory` and `CacheDirectory`. Legacy relative paths (such as `存档.json`) may require a writable working directory; verify file access during initial startup before tightening sandboxing.

## Runtime verification

1. Confirm the executable is an aarch64 ELF, and the package includes `classdata.tpk`, `Data/StreamingAssets` and model assets.
2. Start the server and verify SQLite and ONNX native libraries load.
3. Send the example `POST /simulate` request documented in `PCRCalculatorServer/API.md`.
4. Compare x64 and ARM64 simulation outputs with identical database versions, inputs and random seeds.
5. Stress-test representative concurrent requests and inspect CPU/memory usage and startup reliability.

The ARM64 CI checks packaging and ELF architecture; it does not prove simulation parity or long-running stability. .NET 8 is retained for compatibility; upgrade to a supported LTS framework separately.
