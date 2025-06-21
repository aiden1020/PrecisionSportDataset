# Precision Sport Science Project Dataset

本專案用於國科會精準運動科學研究專案計畫子計劃二，功能包括擊球畫面影片剪輯、caption與QA dataset生成，用於運動影像理解與多模態模型訓練。

## Pipeline 

1. **VideoCropper**
   從原始比賽影片中根據標註 CSV 自動裁剪出包含關鍵擊球動作的短片段。

2. **CaptionGenerator**
   根據裁剪後影片片段及其對應的標註，產生自然語言描述字幕（例如 “upper player hits a serve short in the middle”），並輸出成 CSV 或 JSON 供模型訓練使用。

3. **QAGenerator**
   利用影片片段與字幕，將賽局依 rally 拆分為多個子序列，生成包含正例與負例的問答對（Question-Answer pairs），並自動完成 train/val 資料拆分。


整體流程將上述三個步驟串連，從原始影片一路到最終的 QA dataset，形成一條完整且可重現的資料處理pipline。
>本專案已提供範例 [Demo notebook](Demo.ipynb)，更多實作細節請參考[README](dataset_pipeline/README.md)