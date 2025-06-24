# Precision Sport Science Project Dataset

This project is for the second sub-project of the National Science and Technology Council's Precision Sports Science Research Project. Its functions include clipping video footage of shots, generating captions and QA datasets for sports video understanding and multimodal model training.

## Pipeline 

1. **VideoCropper**
   Automatically crops short clips containing key hitting actions from the original match video based on the annotated CSV.

2. **CaptionGenerator**
   Generates natural language description captions (e.g., "upper player hits a serve short in the middle") based on the cropped video clips and their corresponding annotations, and outputs them as CSV or JSON for model training.

3. **QAGenerator**
   Uses video clips and captions to divide the game into multiple sub-sequences by rally, generates question-answer pairs including positive and negative examples, and automatically completes the train/val data split.


The overall process connects the above three steps, from the original video to the final QA dataset, forming a complete and reproducible data processing pipeline.
>This project provides a [Demo notebook](Demo.ipynb) example. For more implementation details, please refer to [README](dataset_pipeline/README.md)