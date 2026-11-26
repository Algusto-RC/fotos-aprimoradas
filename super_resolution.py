import os
from pathlib import Path
import subprocess
import tempfile

from PIL import Image

from enhance import output_size

AI_PROFILE = "IA local"
MODEL = "realesrgan-x4plus"
NATIVE_SCALE = 4
MAX_NATIVE_PIXELS = 80_000_000


def upscale_with_ai(photo, scale, engine_dir):
    size = output_size(photo, scale)
    native_size = (photo.width * NATIVE_SCALE, photo.height * NATIVE_SCALE)
    if native_size[0] * native_size[1] > MAX_NATIVE_PIXELS or max(native_size) > 16384:
        raise ValueError(
            "A imagem é grande demais para a ampliação interna de 4× da IA. "
            "Reduza a foto original ou use um dos perfis tradicionais."
        )

    executable = engine_dir / ("realesrgan-ncnn-vulkan.exe" if os.name == "nt" else "realesrgan-ncnn-vulkan")
    model_dir = engine_dir / "models"
    if not executable.is_file() or any(not (model_dir / f"{MODEL}.{ext}").is_file() for ext in ("param", "bin")):
        raise RuntimeError("O motor de IA local está incompleto. Reinstale o Fotos Aprimoradas.")

    with tempfile.TemporaryDirectory(prefix="fotos-ia-") as temporary:
        source = Path(temporary) / "original.png"
        target = Path(temporary) / "resultado.png"
        photo.convert("RGB").save(source)
        try:
            subprocess.run(
                [str(executable), "-i", str(source), "-o", str(target),
                 "-m", "models", "-n", MODEL, "-s", str(NATIVE_SCALE), "-f", "png",
                 "-t", "128", "-j", "1:1:1"],
                cwd=engine_dir,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                timeout=900, check=True,
            )
            with Image.open(target) as output:
                if output.size != native_size:
                    raise ValueError("Dimensões inesperadas na saída do modelo.")
                result = output.convert("RGB")
        except subprocess.TimeoutExpired as error:
            raise RuntimeError("A IA excedeu o tempo de processamento. Tente uma foto menor.") from error
        except (OSError, subprocess.CalledProcessError, ValueError) as error:
            raise RuntimeError(
                "A IA local não conseguiu processar a foto. Verifique se a GPU e o driver "
                "suportam Vulkan. Os perfis tradicionais continuam disponíveis."
            ) from error

    if result.size != size:
        result = result.resize(size, Image.Resampling.LANCZOS)
    if photo.mode == "RGBA":
        alpha = photo.getchannel("A").resize(size, Image.Resampling.LANCZOS)
        result.putalpha(alpha)
    if photo.info.get("icc_profile"):
        result.info["icc_profile"] = photo.info["icc_profile"]
    return result
