import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.request import Request, urlopen

VERSION = "1.1.0"
REPOSITORY = "Algusto-RC/fotos-aprimoradas"
INSTALLER = "labGusto-Fotos-Aprimoradas-Setup.exe"


def get_asset():
    endpoint = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
    request = Request(endpoint, headers={"User-Agent": "Fotos-Aprimoradas"})
    with urlopen(request, timeout=20) as response:
        release = json.load(response)
    tag = release["tag_name"]
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError("A versão publicada tem um formato inesperado.")
    if tuple(map(int, tag[1:].split("."))) <= tuple(map(int, VERSION.split("."))):
        return None
    url = f"https://github.com/{REPOSITORY}/releases/download/{tag}/{INSTALLER}"
    for asset in release["assets"]:
        digest = asset.get("digest") or ""
        if asset["browser_download_url"] == url and re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
            return tag, url, digest[7:], int(asset["size"])
    raise ValueError("A atualização ainda não tem um instalador com verificação SHA-256.")


def download_and_launch(asset):
    _, url, expected, size = asset
    if os.name != "nt":
        raise ValueError("O instalador está disponível para Windows.")
    if not 0 < size <= 150 * 1024 * 1024:
        raise ValueError("Tamanho de atualização inesperado.")
    directory = Path(tempfile.mkdtemp(prefix="fotos-aprimoradas-"))
    destination = directory / INSTALLER
    try:
        digest = hashlib.sha256()
        received = 0
        with urlopen(url, timeout=30) as response, destination.open("wb") as output:
            for chunk in iter(lambda: response.read(1024 * 1024), b""):
                received += len(chunk)
                if received > size:
                    raise ValueError("O tamanho do instalador difere da versão publicada.")
                digest.update(chunk)
                output.write(chunk)
        if received != size or digest.hexdigest() != expected:
            raise ValueError("O instalador baixado não passou na verificação SHA-256.")
        os.startfile(destination)
    except Exception:
        destination.unlink(missing_ok=True)
        directory.rmdir()
        raise
