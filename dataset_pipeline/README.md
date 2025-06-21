# Dataset Pipeline README

## 目錄
* [VideoCropper](#videocropper)
* [CaptionGenerator](#captiongenerator)
* [QAGenerator](#qagenerator)

---

## VideoCropper
`VideoCropper` 類別用於根據標註 CSV（`filtered_encoder_data.csv`）中的幀位置資訊，批次從原始影片（`.mp4`）中裁剪片段，並輸出到指定資料夾。

### 輸入

* **原始影片資料夾**：預設路徑為 `Dataset/Video`，影片檔案名稱須與 CSV 中的 `id` 前綴（`<game>`）一致，副檔名為 `.mp4`。
* **標註 CSV**：路徑由 `crop_videos` 方法參數指定，CSV 必須包含 `id` 欄位，格式為 `<game>_<frame_num>`（例如 `NYCU_set1_2400`）。

### 輸出

* **裁剪後影片**：每筆裁剪結果會存成 `<id>.mp4`（例如 `NYCU_set1_2400.mp4`），儲存在建構時指定的 `output_path` 資料夾中。

### 功能說明

#### `__init__(output_path: str, video_dir: str = 'Dataset/Video')`

* **output_path**：裁剪後影片的輸出資料夾路徑。
* **video_dir**：原始影片所在資料夾，預設為 `Dataset/Video`。
* 會自動建立 `output_path` 資料夾（若不存在）。

#### `_crop_video(video_path: str, start_frame: int, end_frame: int, output_path: str, fps: float)`

* **用途**：從 `video_path` 讀取影片，裁剪第 `start_frame` 到 `end_frame` 幀，並依原 FPS 寫入到 `output_path`。
* **參數**：
  * `video_path`：原始影片完整路徑
  * `start_frame`, `end_frame`：裁剪範圍（幀編號）
  * `output_path`：輸出影片完整路徑
  * `fps`：原影片的每秒幀率，用於建立相同速率的輸出影片

#### `crop_videos(csv_path: str)`

* **用途**：批次讀取 `csv_path`，解析每筆資料的 `id`，自動計算裁剪範圍 (`frame_num - 7` 到 `frame_num + 8`)，並呼叫 `_crop_video` 進行裁剪。
* **參數**：
  * `csv_path`：包含 `id` 欄位的 CSV 檔案路徑
* **流程**：
  1. 讀取 CSV，逐行處理
  2. 解析 `game` 與 `frame_num`
  3. 計算 `start_frame` 及 `end_frame`
  4. 讀取影片 FPS
  5. 呼叫 `_crop_video` 輸出裁剪影片

### 範例用法

```python
from video_cropper import VideoCropper

cropper = VideoCropper(output_path='Output', video_dir='Dataset/Video')
cropper.crop_videos('data_processing/processed/filtered_encoder_data.csv')
```

---

## CaptionGenerator

`CaptionGenerator` 類別用於根據標註 CSV（`data_processing/processed/filtered_encoder_data.csv`）產生字幕標籤（caption），並輸出 CSV 供後續訓練使用。

### 輸入

* **標註 CSV**：`data_processing/processed/filtered_encoder_data.csv`，必須包含 `id`、`player`、`stroke_name`、`hit_area` 及 `split` 欄位。

### 輸出

* **Caption CSV**：每筆資料包含以下欄位並存成 `generated_labels/caption/dataset_labels_caption.csv`：
  * `image_id`：原始樣本 ID（如 `NYCU_set1_2400`）
  * `image`：對應影片檔名（如 `NYCU_set1_2400.mp4`）
  * `caption`：自然語言描述（如 `upper player hits a serve short in the middle`）
  * `split`：資料集分割標籤（train/val）

### 功能說明

#### `__init__(output_dir: str)`

* **output_dir**：輸出資料夾路徑，會自動建立（若不存在）。

#### `generate_captions(csv_path: str) -> pd.DataFrame`**

* **用途**：讀取 `csv_path`，逐行解析欄位並組出 caption，最後回傳 pandas DataFrame。
* **參數**：
  * `csv_path`：包含必要欄位的 CSV 檔案路徑
* **流程**：
  1. 讀取 CSV
  2. 對每筆 row：
     - `image_id = row['id']`
     - `image = f"{image_id}.mp4"`
     - `caption = f"{row['player']} hits a {row['stroke_name']} {row['hit_area']}"`
     - `split = row['split']`
  3. 聚合成列表後轉為 DataFrame

### 範例用法

```python
from dataset_pipeline.caption_generator import CaptionGenerator

generator = CaptionGenerator(output_dir='generated_labels/caption')
caption_df = generator.generate_captions('data_processing/processed/filtered_encoder_data.csv')
caption_df.to_csv('generated_labels/caption/dataset_labels_caption.csv', index=False)
print("Caption CSV generated successfully.")
```

---

## QAGenerator

`QAGenerator` 類別用於根據裁剪後的影片片段與 caption CSV，自動生成 QA dataset，並支援 train/val 分割。

### 輸入

* **標註 CSV**：`data_processing/processed/filtered_encoder_data.csv`
* **Caption CSV**：`generated_labels/caption/dataset_labels_caption.csv`

### 輸出

* **QA JSON**：輸出 `generated_labels/QA/qa_dataset.json`
* **Train/Val**：自動生成同目錄下的 `train.json` 與 `val.json`

### 功能說明

#### `__init__(templates_with_all: list, templates_player_stroke: list, templates_stroke_only: list, templates_hit_area_only: list, stroke_chunk_size: int, caption_csv_path: str)`
* 初始化模板、chunk size 及 caption 來源。

#### `generate_by_rally(csv_path: str, output_path: str, num_questions_per_rally: int, val_to_train_ratio: float)`
* **用途**：根據 CSV 中的 `id`、`player`、`stroke_name`、`hit_area` 等欄位，依 rally 分 chunk 生成 QA dataset，最後做 train/val 分割。
* **參數**：
  * `csv_path`：來源 CSV
  * `output_path`：QA JSON 輸出路徑
  * `num_questions_per_rally`：每 chunk 問題數量
  * `val_to_train_ratio`：從 val 移回 train 的比率

### 範例用法

```python
from dataset_pipeline.qa_generator import QAGenerator

templates_all = ["When does the {player} hits a {stroke} {hit_area}?" ]
templates_ps  = ["When does the {player} hits a {stroke}?" ]
templates_s   = ["When is a {stroke} hits?" ]
templates_h   = ["Which stroke is hit {hit_area}?" ]

qa_gen = QAGenerator(
    templates_with_all=templates_all,
    templates_player_stroke=templates_ps,
    templates_stroke_only=templates_s,
    templates_hit_area_only=templates_h,
    stroke_chunk_size=5,
    caption_csv_path='generated_labels/caption/dataset_labels_caption.csv'
)
qa_gen.generate_by_rally(
    csv_path='data_processing/processed/filtered_encoder_data.csv',
    output_path='generated_labels/QA/qa_dataset.json',
    num_questions_per_rally=14,
    val_to_train_ratio=0.05
)
```

---

> **注意**：請先依序執行 `VideoCropper`、`CaptionGenerator`，確保所有影片片段與 caption 已完整產出，才能順利生成 QA dataset。
