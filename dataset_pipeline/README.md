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

`QAGenerator` 類別用於生成兩種類型的 QA dataset：基於筆劃的問答和戰術策略問答，支援 Chain-of-Thought (CoT) 推理和自動 train/val 分割。

### 輸入

* **標註 CSV**：`data_processing/processed/filtered_encoder_data.csv`，必須包含 `id`、`player`、`stroke_name`、`hit_area`、`rally`、`split` 等欄位

### 輸出

* **筆劃 QA JSON**：基於筆劃的問答數據
* **戰術 QA JSON**：基於戰術策略的問答數據  
* **Train/Val**：自動生成訓練集與驗證集分割

### 功能說明

#### `__init__(stroke_chunk_size: int = 10)`

* **stroke_chunk_size**：每個 chunk 的筆劃數量，用於分割 rally 數據

#### `generate_by_rally(csv_path: str, output_path: str, num_questions_per_rally: int = 5, val_to_train_ratio: float = 0.05, use_cot: bool = True)`

* **用途**：生成基於筆劃的 QA dataset，包含四種問題類型：
  * `player_stroke_area`：特定球員在特定區域的特定筆劃
  * `player_stroke`：特定球員的特定筆劃
  * `stroke_only`：特定筆劃類型
  * `hit_area_only`：特定擊球區域的筆劃
* **參數**：
  * `csv_path`：來源 CSV 檔案路徑
  * `output_path`：輸出 JSON 檔案路徑
  * `num_questions_per_rally`：每個 rally chunk 的問題數量
  * `val_to_train_ratio`：從驗證集移回訓練集的比率
  * `use_cot`：是否使用 Chain-of-Thought 推理格式
* **特點**：
  * 自動生成正例和負例問答
  * 支援 CoT 推理，包含分析過程和答案
  * 依據 rally 分 chunk 處理數據

#### `generate_tactical_qa(csv_path: str, output_path: str, val_to_train_ratio: float = 0.05)`

* **用途**：自動偵測並生成戰術策略相關的 QA dataset，支援以下策略：
  * **四角戰術** (`four_corner`)：連續攻擊左右後場角落
  * **網前戰術** (`net_shot`)：連續的網前交換
  * **後場戰術** (`back_court`)：連續的後場深球
  * **平球序列** (`flat_shot_sequence`)：連續的平抽球
  * **反擊戰術** (`counterattack`)：從防守轉攻擊
    * `upper_player_counter_attack`：上方球員反擊
    * `bottom_player_counter_attack`：下方球員反擊
* **參數**：
  * `csv_path`：來源 CSV 檔案路徑  
  * `output_path`：輸出 JSON 檔案路徑
  * `val_to_train_ratio`：資料集分割比率
* **特點**：
  * 自動偵測戰術模式
  * 為每種戰術生成正例和負例問答
  * 支援重疊區段的合併處理
  * 智能分 chunk 以符合模型輸入限制

#### `_detect_strategies(df: pd.DataFrame)`

* **用途**：偵測 rally 中的戰術策略模式
* **偵測策略**：
  * 基於擊球區域的策略（四角、網前、後場）
  * 基於筆劃類型的策略（平球序列）
  * 基於攻防轉換的策略（反擊戰術）

#### `_merge_segments(raw: list, df: pd.DataFrame)`

* **用途**：合併重疊的戰術區段，避免重複標註
* **智能合併**：自動處理時間重疊的戰術模式

### 範例用法

```python
from dataset_pipeline.qa_generator import QAGenerator

# 初始化 QA 生成器
qa_gen = QAGenerator(stroke_chunk_size=10)

# 生成筆劃相關 QA
stroke_qa = qa_gen.generate_by_rally(
    csv_path='data_processing/processed/filtered_encoder_data.csv',
    output_path='generated_labels/stroke_qa.json',
    num_questions_per_rally=14,
    val_to_train_ratio=0.05,
    use_cot=True
)

# 生成戰術策略 QA  
tactical_qa = qa_gen.generate_tactical_qa(
    csv_path='data_processing/processed/filtered_encoder_data.csv',
    output_path='generated_labels/tactical_qa.json',
    val_to_train_ratio=0.05
)

# 合併兩種 QA 數據
combined_qa = tactical_qa + stroke_qa

# 輸出完整 QA dataset
import json
import os
output_path = 'generated_labels/QA_strategy/combined_qa.json'
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(combined_qa, f, ensure_ascii=False, indent=2)
```

### QA 數據格式

每個問答項目包含以下欄位：
* `question_id`：問題唯一 ID
* `image`：相關影片片段檔案列表
* `question`：問題文本
* `answer`：答案（支援 CoT 格式）
* `question_type`：問題類型（筆劃類型或戰術策略）
* `is_impossible`：是否為負例問題
* `split`：資料集分割標籤（train/val）

### Chain-of-Thought 答案格式

```
<thinking>
I need to identify when [objective]. Therefore, we focus on [required_info].
stroke 0: [stroke_info_0]
stroke 1: [stroke_info_1]
...
therefore the answer is [conclusion]
</thinking>
<answer>[final_answer]</answer>
```

---

> **注意**：請先依序執行 `VideoCropper`、`CaptionGenerator`，確保所有影片片段與 caption 已完整產出。`QAGenerator` 現在支援兩種獨立的 QA 生成模式：基於筆劃的問答和戰術策略問答，可以單獨或組合使用以生成完整的多模態問答數據集。
