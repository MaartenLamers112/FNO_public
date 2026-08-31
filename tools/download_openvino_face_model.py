"""Download het officiële OpenVINO-gezichtsdetectiemodel voor FNO."""

from __future__ import annotations

from pathlib import Path
from urllib.request import Request, urlopen

BASE_URL = (
    "https://storage.openvinotoolkit.org/repositories/open_model_zoo/"
    "2023.0/models_bin/1/face-detection-retail-0004/FP16"
)
FILES = (
    "face-detection-retail-0004.xml",
    "face-detection-retail-0004.bin",
)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
TARGET_DIR = PROJECT_ROOT / "app" / "resources"


def download_file(filename: str) -> None:
    """Download één modelbestand wanneer het nog ontbreekt."""

    target = TARGET_DIR / filename
    if target.exists() and target.stat().st_size > 0:
        print(f"OpenVINO-modelbestand is al aanwezig: {target}")
        return

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    request = Request(
        f"{BASE_URL}/{filename}",
        headers={"User-Agent": "Foto-Nummeraar-Online/1.0"},
    )
    with urlopen(request, timeout=60) as response:
        target.write_bytes(response.read())
    print(f"OpenVINO-modelbestand gedownload: {target}")


def main() -> None:
    """Download beide OpenVINO-modelbestanden."""

    for filename in FILES:
        download_file(filename)


if __name__ == "__main__":
    main()
