"""
Script pembantu untuk menghasilkan ikon aplikasi Photo Rename Studio (PNG & ICO).
"""

from pathlib import Path
from PIL import Image, ImageDraw


def generate_app_icons(output_dir: Path | None = None) -> None:
    """Menghasilkan file icon.png dan multi-resolution icon.ico."""
    if output_dir is None:
        project_root = Path(__file__).resolve().parent.parent
        output_dir = project_root / "assets"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Buat kanvas resolusi tinggi 512x512
    size = (512, 512)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Latar belakang persegi membulat (Rounded rectangle) bernuansa biru modern (#2563EB)
    draw.rounded_rectangle([32, 32, 480, 480], radius=96, fill="#2563EB")

    # Badan kamera putih bersih
    draw.rounded_rectangle([96, 140, 416, 380], radius=40, fill="#FFFFFF")

    # Bagian atas / viewfinder kamera
    draw.rounded_rectangle([180, 100, 332, 160], radius=16, fill="#1D4ED8")

    # Lingkaran luar lensa kamera (warna biru sekunder #3B82F6)
    draw.ellipse([176, 180, 336, 340], fill="#3B82F6")

    # Lensa dalam (warna gelap #1E293B)
    draw.ellipse([204, 208, 308, 312], fill="#1E293B")

    # Pantulan cahaya lensa
    draw.ellipse([224, 224, 256, 256], fill="#FFFFFF")

    # Lencana centang/rename hijau di sudut kanan bawah (#10B981)
    draw.ellipse([320, 280, 450, 410], fill="#10B981", outline="#FFFFFF", width=12)

    # Ikon centang putih di dalam badge
    draw.line([350, 345, 375, 370], fill="#FFFFFF", width=12)
    draw.line([375, 370, 420, 315], fill="#FFFFFF", width=12)

    # Resize ke 256x256 untuk kualitas optimal
    icon_256 = img.resize((256, 256), Image.Resampling.LANCZOS)

    png_path = output_dir / "icon.png"
    ico_path = output_dir / "icon.ico"

    icon_256.save(str(png_path), format="PNG")
    icon_256.save(
        str(ico_path),
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )

    print(f"[OK] Ikon berhasil disimpan di:\n  - {png_path}\n  - {ico_path}")


if __name__ == "__main__":
    generate_app_icons()
