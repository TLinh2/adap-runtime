import numpy as np
import os

# ====== CONFIG ======
INPUT_FILE = "data/X_test.npy"      # file gốc
OUTPUT_DIR = "windows"         # thư mục chứa các window

# ====================

# Tạo thư mục nếu chưa có
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Đọc dữ liệu
data = np.load(INPUT_FILE)

print(f"Original shape: {data.shape}")

# Kiểm tra dữ liệu có đúng dạng (N, 1024)
if data.ndim != 2:
    raise ValueError(f"Expected 2D array, got shape {data.shape}")

num_windows = data.shape[0]

# Tách từng window
for i in range(num_windows):
    window = data[i]

    filename = os.path.join(
        OUTPUT_DIR,
        f"window_{i+1:05d}.npy"
    )

    np.save(filename, window)

print(f"\nSaved {num_windows} windows to '{OUTPUT_DIR}'.")

# ==========================
# Verify
# ==========================

print("\nVerifying saved files...")

for i in range(min(5, num_windows)):   # kiểm tra 5 file đầu
    filename = os.path.join(
        OUTPUT_DIR,
        f"window_{i+1:05d}.npy"
    )

    arr = np.load(filename)
    print(f"{os.path.basename(filename)} -> shape {arr.shape}")

print("\nVerification complete.")