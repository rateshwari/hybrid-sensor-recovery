"""Prepare a reproducible, class-balanced EuroSAT RGB dataset."""

import csv
import json
from collections import Counter
from pathlib import Path

from datasets import load_dataset

DATASET_NAME = "blanchon/EuroSAT_RGB"
SPLIT = "train"
IMAGES_PER_CLASS = 50

OUTPUT_DIR = Path("data/satellite/balanced")
MANIFEST_PATH = Path("data/satellite/manifest.csv")
METADATA_PATH = Path("data/satellite/dataset_metadata.json")


def main():
    dataset = load_dataset(
        DATASET_NAME,
        split=SPLIT,
        streaming=True,
    )

    class_names = dataset.features["label"].names
    class_count = len(class_names)

    assert class_count == 10

    counts = Counter()
    records = []

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Dataset: {DATASET_NAME}")
    print(f"Classes: {class_count}")
    print(f"Target: {IMAGES_PER_CLASS} images per class")
    print(f"Total target: {class_count * IMAGES_PER_CLASS}")
    print()

    for index, example in enumerate(dataset):
        label = int(example["label"])

        if counts[label] >= IMAGES_PER_CLASS:
            continue

        image = example["image"].convert("RGB")

        if image.size != (64, 64):
            raise ValueError(
                f"Unexpected image dimensions at index {index}"
            )

        class_dir = OUTPUT_DIR / f"class_{label:02d}"
        class_dir.mkdir(parents=True, exist_ok=True)

        filename = f"eurosat_{index:06d}.png"
        output_path = class_dir / filename

        image.save(output_path)

        records.append({
            "dataset_index": index,
            "original_filename": example["filename"],
            "label": label,
            "class_name": class_names[label],
            "saved_path": str(output_path),
        })

        counts[label] += 1

        if counts[label] == IMAGES_PER_CLASS:
            print(
                f"Completed: {class_names[label]} "
                f"({counts[label]}/{IMAGES_PER_CLASS})",
                flush=True,
            )

        if all(
            counts[i] == IMAGES_PER_CLASS
            for i in range(class_count)
        ):
            break

    if len(records) != class_count * IMAGES_PER_CLASS:
        raise RuntimeError(
            f"Incomplete dataset: collected {len(records)} images"
        )

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    with MANIFEST_PATH.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "dataset_index",
                "original_filename",
                "label",
                "class_name",
                "saved_path",
            ],
        )
        writer.writeheader()
        writer.writerows(records)

    metadata = {
        "dataset": DATASET_NAME,
        "split": SPLIT,
        "images_per_class": IMAGES_PER_CLASS,
        "total_images": len(records),
        "class_names": class_names,
        "sampling": "first 50 encountered per class in dataset order",
    }

    METADATA_PATH.write_text(
        json.dumps(metadata, indent=2)
    )

    print()
    print("Balanced satellite dataset: PASS")
    print(f"Images saved: {len(records)}")
    print(f"Manifest: {MANIFEST_PATH}")
    print(f"Metadata: {METADATA_PATH}")


if __name__ == "__main__":
    main()
