import os

print("=== update start ===")
os.system("python scripts/update_batch.py")

print("=== build light db ===")
os.system("python scripts/build_light_db.py")

print("=== 完了 ===")