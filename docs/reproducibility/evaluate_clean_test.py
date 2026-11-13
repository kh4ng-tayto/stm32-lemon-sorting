
"""
Reproduce YOLOv8s evaluation on the 219-image filtered test set.

Requirements:
    pip install ultralytics==8.4.132

Inputs:
    - Original v4 dataset (243 test images)
    - Final YOLOv8s checkpoint: best.pt
    - exact_duplicates.csv

Outputs:
    - Cleaned test dataset (219 images)
    - clean_test_metrics.csv
    - evaluation_config.json
    - Evaluation plots
"""

import argparse
import csv
import hashlib
import json
import shutil

from pathlib import Path
from collections import Counter
from datetime import datetime, timezone

EXPECTED_SHA256 = (
    "882a065c0d5e4be609dff9150ddeded31b1d996f9dd2700ec637e5def6b0efd2"
)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def get_sha256(path):
    h = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(
            lambda: f.read(1024 * 1024), b""
        ):
            h.update(chunk)

    return h.hexdigest()


def main():

    # =========================================
    # 1. Arguments
    # =========================================

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--v4-root",
        type=Path,
        required=True,
        help="Original v4 dataset folder"
    )

    parser.add_argument(
        "--weights",
        type=Path,
        required=True,
        help="Final best.pt checkpoint"
    )

    parser.add_argument(
        "--exact-csv",
        type=Path,
        default=Path(__file__).resolve().parent
                / "exact_duplicates.csv"
    )

    parser.add_argument(
        "--out",
        type=Path,
        default=Path("reproducibility_output")
    )

    parser.add_argument(
        "--device",
        default="0",
        help="GPU index 0 or cpu"
    )

    args = parser.parse_args()

    # =========================================
    # 2. Check input files
    # =========================================

    src_images = args.v4_root / "test/images"
    src_labels = args.v4_root / "test/labels"

    assert src_images.is_dir(), (
        f"Missing images: {src_images}"
    )

    assert src_labels.is_dir(), (
        f"Missing labels: {src_labels}"
    )

    assert args.weights.is_file(), (
        "Checkpoint best.pt not found"
    )

    assert args.exact_csv.is_file(), (
        "exact_duplicates.csv not found"
    )

    # =========================================
    # 3. Verify checkpoint
    # =========================================

    model_sha256 = get_sha256(args.weights)

    print("Checkpoint SHA-256:", model_sha256)

    assert model_sha256 == EXPECTED_SHA256, (
        "Checkpoint SHA-256 mismatch. "
        "This is not the verified final model."
    )

    # =========================================
    # 4. Read exact duplicate records
    # =========================================

    with open(
        args.exact_csv,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:
        rows = list(csv.DictReader(f))

    required_columns = {
        "test_image",
        "reference_split",
        "match_method"
    }

    assert rows, "Duplicate CSV is empty"
    assert required_columns.issubset(rows[0]), (
        "Unexpected duplicate CSV columns"
    )

    duplicates = set()

    for row in rows:

        split = row["reference_split"].strip().lower()
        method = row["match_method"].strip()

        if (
            split in {"val", "valid", "validation"}
            and method in {"file_sha256", "pixel_sha256"}
        ):
            duplicates.add(
                Path(row["test_image"]).name
            )

    print("Exact duplicates:", len(duplicates))

    assert len(duplicates) == 24, (
        "Expected exactly 24 duplicate images"
    )

    # =========================================
    # 5. Read original v4 test set
    # =========================================

    images = sorted(
        p for p in src_images.iterdir()
        if p.is_file()
        and p.suffix.lower() in IMAGE_EXTENSIONS
    )

    assert len(images) == 243, (
        f"Expected 243 images, found {len(images)}"
    )

    original_names = {p.name for p in images}

    assert duplicates.issubset(original_names), (
        "Duplicate records do not match v4 dataset"
    )

    # =========================================
    # 6. Create filtered dataset
    # =========================================

    output = args.out.resolve()
    clean_root = output / "clean_v4_test"

    if clean_root.exists():
        shutil.rmtree(clean_root)

    dest_images = clean_root / "test/images"
    dest_labels = clean_root / "test/labels"

    dest_images.mkdir(parents=True)
    dest_labels.mkdir(parents=True)

    counts = Counter()
    kept = 0

    for image in images:

        if image.name in duplicates:
            continue

        label = src_labels / f"{image.stem}.txt"

        if not label.is_file():
            raise FileNotFoundError(
                f"Missing label: {label.name}"
            )

        # Count annotated instances
        for line in label.read_text(
            encoding="utf-8"
        ).splitlines():

            if not line.strip():
                continue

            parts = line.split()

            if len(parts) != 5:
                raise ValueError(
                    f"Invalid YOLO label: {label.name}"
                )

            class_id = int(parts[0])

            if class_id not in (0, 1):
                raise ValueError(
                    f"Invalid class: {class_id}"
                )

            counts[class_id] += 1

        shutil.copy2(
            image,
            dest_images / image.name
        )

        shutil.copy2(
            label,
            dest_labels / label.name
        )

        kept += 1

    print("\n=== FILTERED DATASET ===")
    print("Images:", kept)
    print("Bad:", counts[0])
    print("Good:", counts[1])
    print("Total objects:", sum(counts.values()))

    assert kept == 219
    assert counts[0] == 206
    assert counts[1] == 35
    assert sum(counts.values()) == 241

    # =========================================
    # 7. Create YOLO data.yaml
    # =========================================

    yaml_path = clean_root / "data.yaml"

    yaml_path.write_text(
        f"""path: {clean_root.as_posix()}
train: test/images
val: test/images
test: test/images
nc: 2
names:
  0: Bad
  1: Good
""",
        encoding="utf-8"
    )

    # =========================================
    # 8. Load YOLOv8s
    # =========================================

    import ultralytics
    from ultralytics import YOLO

    assert ultralytics.__version__ == "8.4.132", (
        "Required ultralytics==8.4.132"
    )

    model = YOLO(str(args.weights))

    assert str(model.names.get(0)).lower() == "bad"
    assert str(model.names.get(1)).lower() == "good"

    # =========================================
    # 9. Evaluate filtered test set
    # =========================================

    print("\n=== RUNNING EVALUATION ===")

    results = model.val(
        data=str(yaml_path),
        split="test",
        imgsz=320,
        conf=0.001,
        iou=0.7,
        batch=16,
        device=args.device,
        plots=True,
        project=str(output),
        name="evaluation_219",
        exist_ok=True
    )

    # =========================================
    # 10. Export metrics
    # =========================================

    metrics = {
        "model": "YOLOv8s",
        "images": kept,
        "instances": sum(counts.values()),
        "bad_instances": counts[0],
        "good_instances": counts[1],
        "removed_exact_duplicates": len(duplicates),
        "imgsz": 320,
        "confidence": 0.001,
        "nms_iou": 0.7,
        "batch": 16,
        "ultralytics_version": ultralytics.__version__,
        "precision": float(results.box.mp),
        "recall": float(results.box.mr),
        "mAP50": float(results.box.map50),
        "mAP50_95": float(results.box.map),
        "checkpoint_sha256": model_sha256,
        "evaluated_at_utc": datetime.now(
            timezone.utc
        ).isoformat()
    }

    output.mkdir(parents=True, exist_ok=True)

    csv_path = output / "clean_test_metrics.csv"

    with open(
        csv_path,
        "w",
        encoding="utf-8",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=list(metrics.keys())
        )

        writer.writeheader()
        writer.writerow(metrics)

    config_path = output / "evaluation_config.json"

    config_path.write_text(
        json.dumps(
            {
                "weights": str(args.weights.resolve()),
                "v4_root": str(args.v4_root.resolve()),
                "exact_csv": str(args.exact_csv.resolve()),
                "metrics": metrics
            },
            indent=2
        ),
        encoding="utf-8"
    )

    # =========================================
    # 11. Final results
    # =========================================

    print("\n=== FINAL RESULTS ===")

    for key in [
        "precision",
        "recall",
        "mAP50",
        "mAP50_95"
    ]:
        print(f"{key}: {metrics[key]:.6f}")

    print("\nSaved:", csv_path)
    print("Saved:", config_path)
    print("Evaluation plots:", results.save_dir)

    print("\nEvaluation completed successfully!")


if __name__ == "__main__":
    main()
