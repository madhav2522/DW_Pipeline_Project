# generate_large_students_csv.py
import csv
import os
import random
import string

# Config
OUTPUT_DIR = "../data"
OUTPUT_FILE = "students_large.csv"  # or split into many files
TARGET_SIZE_GB = 5
BATCH_ROWS = 1_000_000  # adjust for your system's memory

os.makedirs(OUTPUT_DIR, exist_ok=True)
output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

def random_name():
    return ''.join(random.choices(string.ascii_letters, k=random.randint(5, 10)))

def random_city():
    return random.choice(["Cleveland", "Dayton", "Akron", "Toledo", "Cincinnati", "Columbus", "Springfield", "Youngstown"])

with open(output_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["student_id", "name", "age", "city"])  # header

    student_id = 1
    while os.path.getsize(output_path) < TARGET_SIZE_GB * (1024**3):
        batch = []
        for _ in range(BATCH_ROWS):
            batch.append([
                student_id,
                random_name(),
                random.randint(18, 30),
                random_city()
            ])
            student_id += 1
        writer.writerows(batch)
        print(f"Current size: {os.path.getsize(output_path) / (1024**3):.2f} GB")

print(f"✅ Done! File generated at {output_path}, size: {os.path.getsize(output_path) / (1024**3):.2f} GB")
