import numpy as np

rng = np.random.default_rng(0)  # pembuat noise acak
print(rng.normal(0, 0.02, size=8))

# Jarak asli ruangan di 8 zona (sistem nggak tahu nilai ini)
ruangan_asli = np.array([2.0, 2.0, 2.0, 2.4, 2.4, 3.0, 3.0, 3.0])

# Peta awal masih ngawur: semua zona ditebak 1 m
peta = np.ones(8)
print(peta)

learning_rate = 0.2  # seberapa besar koreksi tiap putaran

for putaran in range(31):
    # Sensor ToF: jarak asli + noise sekitar 2 cm
    tof = ruangan_asli + rng.normal(0, 0.02, size=8)

    # "Render": di versi mini ini, tebakan langsung dibaca dari peta
    rendered = peta.copy()

    # Selisih tebakan vs. sensor, dan loss-nya (mirip L_z)
    selisih = rendered - tof
    loss = np.mean(np.abs(selisih))
    print(f'xxx Putaran {putaran:2d}: loss = {loss:.3f} m  selisih = {selisih.round(2)}')

    # Koreksi: geser peta sedikit ke arah data sensor
    peta = peta - learning_rate * selisih

    if putaran % 5 == 0:
        print(f"Putaran {putaran:2d}: loss = {loss:.3f} m")

print("Peta akhir  :", peta.round(2))
print("Ruangan asli:", ruangan_asli)