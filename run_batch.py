import os

print("=== update start ===")
os.system("python update_batch.py")

print("=== build light db ===")
os.system("python build_light_db.py")

print("=== 完了 ===")