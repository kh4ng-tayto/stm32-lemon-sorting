
# Reproducibility Materials

This directory provides an index of the experimental
materials for the YOLOv8s and STM32-based lemon sorting system.

## 1. Source Code

- Python vision application:
  [vision/](../../vision/)

- STM32 firmware and peripheral configuration:
  [firmware/](../../firmware/)

- Hardware specifications and wiring:
  [docs/hardware/](../hardware/)

## 2. Model Checkpoint

The final YOLOv8s checkpoint is available from GitHub Releases:

[Download best.pt](https://github.com/kh4ng-tayto/stm32-lemon-sorting/releases/download/v1.0-model/best.pt)

Checkpoint SHA-256:

882a065c0d5e4be609dff9150ddeded31b1d996f9dd2700ec637e5def6b0efd2

The checksum should be verified against the downloaded
checkpoint before reproducing the evaluation.

## 3. Training Configuration and Logs

The original training configuration and epoch-level
results are available in:

- [Training documentation](../training/README.md)
- [Training arguments](../training/args%20(1).yaml)
- [Epoch-level results](../training/results.csv)

The YOLOv8s training used:

- Maximum epochs: 120
- Recorded epochs: 118
- Best epoch: 93
- Batch size: 16
- Training image size: 640
- Random seed: 42
- Early stopping patience: 25

## 4. Dataset and Evaluation

Dataset information is available in:

[Dataset documentation](../datasets/README.md)

The supplementary v4 evaluation used:

- Original test set: 243 images
- Exact duplicates removed: 24 images
- Filtered test set: 219 images
- Annotated objects: 241
- Evaluation image size: 320
- Confidence threshold: 0.001
- NMS IoU threshold: 0.7
- Ultralytics: 8.4.132

Results on the filtered test set:

| Metric | Value |
|---|---:|
| Precision | 0.9337 |
| Recall | 0.9622 |
| mAP50 | 0.9860 |
| mAP50:95 | 0.8479 |

The dataset audit identified image-level overlap.
Complete physical-fruit independence was not established.

## 5. Latency Measurement Records

The available event-level measurement logs are stored in:

[Latency logs](../latency_logs/)

They contain measurements collected at:

- 10 FPS
- 15 FPS
- 20 FPS

The available records contain 41 measurement events.
These records support analysis of the logged latency
components but do not represent direct power measurements.

## 6. Software Environment

The inspected Kaggle evaluation environment included:

- Python 3.12.13
- PyTorch 2.10.0+cu128
- CUDA 12.8
- Ultralytics 8.4.132
- OpenCV 4.13.0.92
- NumPy 2.4.6
- Pandas 2.3.3
- Torchvision 0.25.0+cu128
- NVIDIA Tesla T4 GPU

These versions describe the inspected evaluation
environment and are not necessarily identical to the
original training environment.

## 7. Limitations

The following limitations apply:

- Physical fruit identifiers were not available.
- Direct power consumption measurements were not recorded.
- Full physical-system reproduction requires the original
  hardware or an equivalent setup.
- Reproducing detection metrics requires access to the
  corresponding annotated datasets and filtering records.
- The availability of latency logs does not independently
  establish every hardware timing characteristic.

The provided materials support code inspection,
configuration review, and independent verification of
the documented experiments where the required data
and equipment are available.

## 8. Reproducing the Filtered Test Evaluation

The evaluation script is available at:

[evaluate_clean_test.py](evaluate_clean_test.py)

### Required Inputs

- Original v4 dataset with 243 test images and YOLO labels
- Final YOLOv8s checkpoint (`best.pt`)
- [Exact duplicate records](exact_duplicates.csv)

The original image and annotation files are required
to reproduce the reported detection metrics.

### Installation

Install the required Ultralytics version:

```bash
pip install ultralytics==8.4.132
```

### Run Evaluation

From the repository root, execute:

```bash
python docs/reproducibility/evaluate_clean_test.py \
  --v4-root /path/to/v4_dataset \
  --weights /path/to/best.pt \
  --device 0
```

Replace the example paths with the actual dataset and
checkpoint locations.

For CPU-only environments, use `--device cpu`.

### Expected Results

The script removes 24 exact-overlap images and evaluates
the remaining 219 images containing 241 annotations.

| Metric | Expected value |
|---|---:|
| Precision | 0.9337 |
| Recall | 0.9622 |
| mAP50 | 0.9860 |
| mAP50:95 | 0.8479 |

The evaluation generates:

- `clean_test_metrics.csv`
- `evaluation_config.json`
- Evaluation plots

Results are saved under `reproducibility_output/`.

### Dataset Audit

Additional supporting materials include:

- [Dataset manifest](dataset_manifest.csv)
- [Exact duplicates](exact_duplicates.csv)
- [Near-duplicate candidates](near_duplicates.csv)
- [Near-duplicate review image](near_duplicate_review.png)

The script removes exact duplicates only. It does not
remove all near-duplicates or establish physical-fruit
independence.
```

