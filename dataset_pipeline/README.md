## VideoCropper

### 目的

`VideoCropper` 類別用於根據標註 CSV（`filtered_encoder_data.csv`）中的幀位置資訊，批次從原始影片（`.mp4`）中裁剪片段，並輸出到指定資料夾。

### 輸入

* **原始影片資料夾**：預設路徑為 `Dataset/Video`，影片檔案名稱須與 CSV 中的 `id` 前綴（`<game>`）一致，副檔名為 `.mp4`。
* **標註 CSV**：路徑與檔名由 `crop_videos` 方法參數指定，CSV 必須包含 `id` 欄位，格式為 `<game>_<frame_num>`（例如 `NYCU_set1_2400`）。

### 輸出

* **裁剪後影片**：會將每筆裁剪結果存成 `<id>.mp4`（例如 `NYCU_set1_2400.mp4`），儲存在建構時指定的 `output_path` 資料夾中。

### 功能說明

#### `__init__(output_path: str, video_dir: str = 'Dataset/Video')`

* **output\_path**：裁剪後影片的輸出資料夾路徑。
* **video\_dir**：原始影片所在資料夾，預設為 `Dataset/Video`。
* 會自動建立 `output_path` 資料夾（若不存在）。

#### `_crop_video(video_path: str, start_frame: int, end_frame: int, output_path: str, fps: float)`

* **用途**：從 `video_path` 讀取影片，裁剪第 `start_frame` 到 `end_frame` 幀之間的內容，並以 `fps` 寫入到 `output_path`。
* **參數**：

  * `video_path`：原始影片完整路徑
  * `start_frame`, `end_frame`：裁剪範圍（幀編號）
  * `output_path`：輸出影片完整路徑
  * `fps`：原影片的每秒幀率，用於建立相同速率的輸出影片

#### `crop_videos(csv_path: str)`

* **用途**：批次讀取 `csv_path`，解析每筆資料的 `id`，自動計算裁剪範圍（`frame_num - 7` 到 `frame_num + 8`），並調用 `_crop_video` 進行裁剪。
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

# 1. 建立 VideoCropper
cropper = VideoCropper(output_path='Output', video_dir='Dataset/Video')

# 2. 執行批次裁剪
cropper.crop_videos('filtered_encoder_data.csv')
```

執行後，裁剪後的影片檔案會存放在 `Output/` 資料夾中，每個檔名對應為 `<id>.mp4`。

---
