from PIL import Image, ImageFilter, ImageOps

FORMATS = {"JPEG", "PNG", "WEBP", "BMP", "TIFF"}
MAX_PIXELS = 40_000_000


def load_photo(path):
    with Image.open(path) as source:
        if source.format not in FORMATS or getattr(source, "n_frames", 1) != 1:
            raise ValueError("Selecione uma imagem estática JPG, PNG, WebP, BMP ou TIFF.")
        if source.width * source.height > MAX_PIXELS:
            raise ValueError("A foto excede 40 megapixels.")
        photo = ImageOps.exif_transpose(source)
        if "A" in photo.getbands() or "transparency" in photo.info:
            return photo.convert("RGBA")
        return photo.convert("RGB")


def enhance(photo, scale, profile="Equilibrado"):
    if scale not in (1, 2, 3, 4):
        raise ValueError("Selecione uma ampliação entre 1× e 4×.")
    width, height = photo.width * scale, photo.height * scale
    if width * height > MAX_PIXELS or max(width, height) > 16384:
        raise ValueError("A saída excede 40 megapixels ou 16.384 px por lado. Tente uma escala menor.")

    noise, edge_strength, texture_strength, threshold = {
        "Suave": (0.45, 75, 30, 5),
        "Equilibrado": (0.20, 100, 43, 4),
        "Detalhes": (0.0, 125, 46, 3),
    }[profile]
    luma, cb, cr = photo.convert("RGB").convert("YCbCr").split()
    if noise:
        luma = Image.blend(luma, luma.filter(ImageFilter.MedianFilter(3)), noise)

    # Work at source resolution first so edge correction survives enlargement.
    luma = luma.filter(ImageFilter.UnsharpMask(radius=1.1, percent=edge_strength, threshold=threshold))
    luma = luma.filter(ImageFilter.UnsharpMask(radius=3.2, percent=texture_strength, threshold=threshold + 2))
    corrected = Image.merge("YCbCr", (luma, cb, cr)).convert("RGB")
    if photo.mode == "RGBA":
        corrected.putalpha(photo.getchannel("A"))
    result = corrected.resize((width, height), Image.Resampling.LANCZOS)
    if photo.info.get("icc_profile"):
        result.info["icc_profile"] = photo.info["icc_profile"]
    return result


def save_photo(photo, path):
    import os
    import tempfile
    from pathlib import Path

    target = Path(path)
    suffix = target.suffix.lower()
    options = {}
    if photo.info.get("icc_profile"):
        options["icc_profile"] = photo.info["icc_profile"]
    if suffix in {".jpg", ".jpeg"}:
        if photo.mode == "RGBA":
            background = Image.new("RGB", photo.size, "white")
            background.paste(photo, mask=photo.getchannel("A"))
            photo = background
        options.update(quality=95, subsampling=0)
    elif suffix == ".webp":
        options["lossless"] = True
    elif suffix != ".png":
        raise ValueError("Escolha PNG, JPG ou WebP para salvar.")
    with tempfile.NamedTemporaryFile(dir=target.parent, suffix=suffix, delete=False) as temp:
        temporary = temp.name
    try:
        photo.save(temporary, **options)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
