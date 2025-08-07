# Precision Sport Science Project Dataset

This project is for the second sub-project of the National Science and Technology Council's Precision Sports Science Research Project. Its functions include clipping video footage of shots, generating captions and QA datasets for sports video understanding and multimodal model training.

## Pipeline 

1. **VideoCropper** 
   Automatically crops short clips containing key hitting actions from the original match video based on the annotated CSV.

2. **CaptionGenerator**
   Generates natural language description captions (e.g., "upper player hits a serve short in the middle") based on the cropped video clips and their corresponding annotations, and outputs them as CSV or JSON for model training.

3. **QAGenerator**
   Advanced QA dataset generator with two main modes:
   - **Stroke-based QA**: Generates questions about specific strokes, players, and hit areas within rally chunks, supporting both positive and negative examples with Chain-of-Thought (CoT) reasoning
   - **Tactical QA**: Automatically detects and generates questions about advanced badminton strategies including four-corner patterns, net shots, back-court rallies, flat-shot sequences, and counter-attacks
   - Supports automatic train/val data splitting and configurable chunk sizes


The overall process connects the above three steps, from the original video to the final QA dataset, forming a complete and reproducible data processing pipeline.
>This project provides a [Demo notebook](Demo.ipynb) example. For more implementation details, please refer to [README](dataset_pipeline/README.md)