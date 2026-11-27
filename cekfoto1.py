from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS, IFD

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIC_AKTIF = True
except ImportError:
    HEIC_AKTIF = False


def ambil_exif(path):
    with Image.open(path) as img:
        raw = img.getexif()
        if not raw:
            return None

        exif_dict = dict(raw)

        try:
            gps_ifd = raw.get_ifd(IFD.GPSInfo)
            if gps_ifd:
                exif_dict[34853] = dict(gps_ifd)
        except Exception:
            pass

    data = {}
    for tag_id, value in exif_dict.items():
        tag = TAGS.get(tag_id, tag_id)
        data[tag] = value

    return data


def ambil_gps(exif):
    if not exif or "GPSInfo" not in exif:
        return None

    gps_raw = exif["GPSInfo"]
    if not isinstance(gps_raw, dict):
        return None

    gps = {}
    for key, value in gps_raw.items():
        nama = GPSTAGS.get(key, key)
        gps[nama] = value

    return gps


def _ke_float(nilai):
    # Menangani nilai berupa tuple/IFDRational atau angka langsung
    if hasattr(nilai, "numerator") and hasattr(nilai, "denominator"):
        return float(nilai.numerator) / float(nilai.denominator)
    return float(nilai)


def ke_derajat(nilai):
    d, m, s = nilai
    return _ke_float(d) + (_ke_float(m) / 60.0) + (_ke_float(s) / 3600.0)


def koordinat_desimal(gps):
    if not gps:
        return None

    if "GPSLatitude" not in gps or "GPSLongitude" not in gps:
        return None

    try:
        lat = ke_derajat(gps["GPSLatitude"])
        lon = ke_derajat(gps["GPSLongitude"])
    except (TypeError, ValueError, ZeroDivisionError):
        return None

    if gps.get("GPSLatitudeRef") == "S":
        lat = -lat

    if gps.get("GPSLongitudeRef") == "W":
        lon = -lon

    return lat, lon


def cek_satu_foto(path):
    print("=" * 55)
    print(f"FOTO : {path}")
    print("=" * 55)

    try:
        exif = ambil_exif(path)
    except FileNotFoundError:
        print("File tidak ditemukan.\n")
        return
    except Exception as e:
        if path.lower().endswith(".heic") and not HEIC_AKTIF:
            print("Foto HEIC belum didukung.")
            print("Install terlebih dahulu:")
            print("pip install pillow-heif\n")
        else:
            print(f"Gagal membaca foto: {e}\n")
        return

    if not exif:
        print("Foto tidak memiliki metadata EXIF.\n")
        return

    kamera = exif.get("Make", "")
    model = exif.get("Model", "")
    waktu = exif.get("DateTimeOriginal") or exif.get("DateTime", "")

    if kamera or model:
        print(f"Perangkat : {str(kamera).strip()} {str(model).strip()}".strip())

    if waktu:
        print(f"Tanggal   : {waktu}")

    gps = ambil_gps(exif)
    koor = koordinat_desimal(gps)

    if koor:
        lat, lon = koor
        print("\nGPS ditemukan")
        print(f"Latitude    : {lat:.6f}")
        print(f"Longitude   : {lon:.6f}")
        print(f"Google Maps : https://www.google.com/maps?q={lat},{lon}")
    else:
        print("\nMetadata GPS tidak ditemukan.")

    print()


def main():
    while True:
        path = input("Masukin nama fotonya (exit untuk keluar): ").strip()

        if path.lower() in ("exit", "quit", "q"):
            break

        if not path:
            continue

        cek_satu_foto(path)


if __name__ == "__main__":
    main()