"""Simulasi iterasi seperti simulasi_iterasi.py, tapi pakai data ToF asli.

Tiap putaran memakai satu frame berikutnya dari dataset. Bagian kamera di frame
ini hampir diam (geser sekitar 4 cm), jadi peta 8x8 masih boleh dianggap melihat
area yang sama. Ini penyederhanaan: paper menyimpan peta dalam 3D.

Cara pakai (dari folder tof-slam):
    python code/simulasi_iterasi_dataset.py

Hasil tersimpan di folder output/: satu GIF dan satu PNG.
"""
import glob  # mencari file berdasarkan pola nama
import os    # mengolah path dan nama file

import h5py  # membaca file .h5 (satu file = satu frame)
import matplotlib.pyplot as plt  # menggambar grafik
import numpy as np
from matplotlib.animation import PillowWriter  # menyimpan animasi jadi GIF
from matplotlib.colors import LinearSegmentedColormap

# ----- Yang boleh lo ubah -----
SEQUENCE = "dataset/ZJUL5-SLAM/Sofa2"
START_FRAME = 490      # bagian Sofa2 yang kameranya hampir diam
N_PUTARAN = 30         # satu putaran = satu frame
LEARNING_RATE = 0.2    # seberapa besar koreksi tiap putaran
PETA_AWAL = 1.0        # tebakan awal semua zona, dalam meter

# ----- Warna grafik -----
BIRU = "#2a78d6"
ORANYE = "#eb6834"
ABU_ABU = "#e1e0d9"    # zona tanpa data
TINTA = "#52514e"      # warna teks
SKALA_JARAK = LinearSegmentedColormap.from_list(
    "jarak", ["#cde2fb", "#6da7ec", "#256abf", "#0d366b"])  # dekat = terang
SKALA_JARAK.set_bad(ABU_ABU)  # nilai NaN digambar abu-abu
JARAK_MIN, JARAK_MAX = 0.8, 2.0  # semua panel memakai skala warna yang sama


def timestamp_of(path):
    """Ubah '.../1656938733.270982.h5' menjadi angka 1656938733.270982."""
    return float(os.path.basename(path)[:-len(".h5")])


def baca_frame(path):
    """Baca semua data satu frame yang dipakai simulasi ini."""
    with h5py.File(path, "r") as frame:
        return (frame["rgb"][()], frame["hist_data"][()][:, 0], frame["mask"][()],
                frame["fr"][()], frame["depth"][()])


def jawaban_realsense(depth, fr):
    """Hitung jarak rata-rata RealSense di tiap zona. Cuma buat menilai hasil."""
    jawaban = np.full(64, np.nan)  # NaN artinya "tidak ada jawaban"
    for zona in range(64):
        y_min, x_min, y_max, x_max = fr[zona]
        # Baris zona pertama ada di luar gambar (y negatif), jadi dipotong dan kosong
        piksel = depth[max(y_min, 0):max(y_max, 0), max(x_min, 0):max(x_max, 0)]
        piksel = piksel[(piksel > 0) & (piksel < 10)]  # buang depth yang tidak masuk akal
        if piksel.size > 50:
            jawaban[zona] = piksel.mean()
    return jawaban


def gambar_8x8(ax, nilai, judul):
    """Gambar 64 nilai sebagai kotak 8x8, lalu kembalikan objek gambarnya."""
    gambar = ax.imshow(nilai.reshape(8, 8), cmap=SKALA_JARAK, vmin=JARAK_MIN, vmax=JARAK_MAX)
    ax.set_title(judul, fontsize=11, color=TINTA)
    ax.set_xticks([])
    ax.set_yticks([])
    return gambar


# Kumpulkan frame dan urutkan berdasarkan waktu
paths = sorted(glob.glob(os.path.join(SEQUENCE, "Raw", "*.h5")), key=timestamp_of)
paths = paths[START_FRAME:START_FRAME + N_PUTARAN]
if len(paths) < N_PUTARAN:
    raise SystemExit(f"Frame tidak cukup di {SEQUENCE}. Jalankan dari folder tof-slam.")

# Peta awal masih ngawur: semua zona ditebak sama
peta = np.full(64, PETA_AWAL)
sudah_dikoreksi = np.zeros(64, dtype=bool)  # zona yang pernah dapat data valid
riwayat_loss = []
riwayat_error = []

# ----- Siapkan jendela: 4 gambar di atas, 1 grafik di bawah -----
fig = plt.figure(figsize=(12, 6.5))
grid = fig.add_gridspec(2, 4, height_ratios=[1.15, 1], hspace=0.28, wspace=0.08,
                        left=0.06, right=0.91, top=0.9, bottom=0.09)
ax_rgb, ax_peta, ax_sensor, ax_jawaban = [fig.add_subplot(grid[0, i]) for i in range(4)]
ax_grafik = fig.add_subplot(grid[1, :])
judul_utama = fig.suptitle("", fontsize=13, color=TINTA)

rgb, _, _, fr, _ = baca_frame(paths[0])
gambar_rgb = ax_rgb.imshow(rgb)
ax_rgb.set_title("Kamera dan zona ToF", fontsize=11, color=TINTA)
ax_rgb.set_xticks([])
ax_rgb.set_yticks([])
for y_min, x_min, y_max, x_max in fr:
    # Gambar kotak tiap zona. Baris pertama di luar gambar, jadi tidak ikut tampil
    ax_rgb.add_patch(plt.Rectangle((x_min, y_min), x_max - x_min, y_max - y_min,
                                   fill=False, edgecolor="white", linewidth=0.5))
ax_rgb.set_xlim(0, 640)
ax_rgb.set_ylim(480, 0)

kosong = np.full(64, np.nan)
gambar_peta = gambar_8x8(ax_peta, kosong, "Peta (tebakan)")
gambar_sensor = gambar_8x8(ax_sensor, kosong, "Sensor ToF frame ini")
gambar_jawaban = gambar_8x8(ax_jawaban, kosong, "Kunci jawaban (RealSense)")
tanda_silang, = ax_sensor.plot([], [], "x", color=TINTA, markersize=6)  # zona tidak valid

# Skala warna di sisi kanan
skala_ax = fig.add_axes([0.925, 0.53, 0.012, 0.36])
fig.colorbar(gambar_jawaban, cax=skala_ax, label="Jarak (m)")

# Grafik garis: makin rendah makin bagus
garis_loss, = ax_grafik.plot([], [], color=BIRU, linewidth=2,
                             label="Loss: selisih peta dengan sensor (dipakai untuk koreksi)")
garis_error, = ax_grafik.plot([], [], color=ORANYE, linewidth=2,
                              label="Error: selisih peta dengan RealSense (cuma penilaian)")
ax_grafik.set_xlim(0, N_PUTARAN - 1)
ax_grafik.set_xlabel("Putaran", color=TINTA)
ax_grafik.set_ylabel("Selisih rata-rata (m)", color=TINTA)
ax_grafik.grid(axis="y", color=ABU_ABU, linewidth=0.8)
ax_grafik.set_axisbelow(True)
ax_grafik.spines[["top", "right"]].set_visible(False)
ax_grafik.tick_params(colors=TINTA)
ax_grafik.legend(loc="upper right", frameon=False, fontsize=10)

# ----- Iterasi: sama seperti simulasi_iterasi.py -----
os.makedirs("output", exist_ok=True)
penyimpan_gif = PillowWriter(fps=4)
with penyimpan_gif.saving(fig, "output/iterasi_dataset.gif", dpi=80):
    for putaran, path in enumerate(paths):
        rgb, tof, valid, fr, depth = baca_frame(path)
        jawaban = jawaban_realsense(depth, fr)

        # 1. Tebak: di versi mini ini, tebakan langsung dibaca dari peta
        rendered = peta.copy()

        # 2. Bandingkan, tapi hanya di zona valid (seperti L_z pada Eq. 7)
        selisih = rendered[valid] - tof[valid]
        loss = np.mean(np.abs(selisih))
        ada_jawaban = ~np.isnan(jawaban)
        error = np.mean(np.abs(rendered[ada_jawaban] - jawaban[ada_jawaban]))
        riwayat_loss.append(loss)
        riwayat_error.append(error)
        if putaran == 0:
            # Sesuaikan tinggi grafik dengan selisih awal, yang biasanya paling besar
            ax_grafik.set_ylim(0, max(loss, error) * 1.25)
        print(f"Putaran {putaran:2d}: zona valid = {valid.sum():2d}/64  "
              f"loss = {loss:.3f} m  error = {error:.3f} m")

        # Perbarui gambar. Zona tidak valid dibuat NaN supaya tampil abu-abu
        sensor_tampil = tof.copy()
        sensor_tampil[~valid] = np.nan
        gambar_rgb.set_data(rgb)
        gambar_peta.set_data(rendered.reshape(8, 8))
        gambar_sensor.set_data(sensor_tampil.reshape(8, 8))
        gambar_jawaban.set_data(jawaban.reshape(8, 8))
        baris_kosong, kolom_kosong = np.where(~valid.reshape(8, 8))
        tanda_silang.set_data(kolom_kosong, baris_kosong)
        sumbu_x = np.arange(len(riwayat_loss))
        garis_loss.set_data(sumbu_x, riwayat_loss)
        garis_error.set_data(sumbu_x, riwayat_error)
        judul_utama.set_text(f"Putaran {putaran}: peta dikoreksi dengan data ToF asli "
                             f"(learning rate = {LEARNING_RATE})")
        penyimpan_gif.grab_frame()
        plt.pause(0.05)  # beri waktu supaya jendela sempat menggambar

        # 3. Koreksi: geser peta ke arah sensor, hanya di zona valid
        peta[valid] = peta[valid] - LEARNING_RATE * selisih
        sudah_dikoreksi[valid] = True

fig.savefig("output/iterasi_dataset.png", dpi=120)

np.set_printoptions(precision=2, suppress=True, linewidth=100)
print("\nPeta akhir (m):")
print(peta.reshape(8, 8))
print("\nKunci jawaban frame terakhir (m), baris pertama di luar gambar:")
print(jawaban.reshape(8, 8))
print(f"\nZona yang tidak pernah dapat data valid: {(~sudah_dikoreksi).sum()}")
print("Tersimpan: output/iterasi_dataset.gif dan output/iterasi_dataset.png")

plt.show()  # jendela tetap terbuka sampai lo tutup
