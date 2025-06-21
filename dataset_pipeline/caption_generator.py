import os
import pandas as pd
from tqdm import tqdm
import json
class CaptionGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def generate_captions(self, csv_path: str) -> None:
        """
        根據標註 CSV 產生 train/val JSON 檔，並生成 val_gt.json 格式：
        {
            "annotations": [...],
            "images": [...]
        }
        """
        df = pd.read_csv(csv_path)
        captions = []
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Generating captions"):
            image_id = row['id']
            image = f"{image_id}.mp4"
            caption = f"{row['player']} hits a {row['stroke_name']} {row['hit_area']}"
            split = row['split']
            captions.append({
                'image_id': image_id,
                'image': image,
                'caption': caption,
                'split': split
            })
        df_caps = pd.DataFrame(captions)

        # 分 train / val
        train_df = df_caps[df_caps['split'] == 'train']
        val_df = df_caps[df_caps['split'] == 'val']

        # 產生 train.json, val.json
        train_data = train_df[['caption', 'image', 'image_id']].to_dict(orient='records')
        val_data = val_df[['caption', 'image', 'image_id']].to_dict(orient='records')

        with open(os.path.join(self.output_dir, 'train.json'), 'w', encoding='utf-8') as f:
            json.dump(train_data, f, ensure_ascii=False, indent=4)
        with open(os.path.join(self.output_dir, 'val.json'), 'w', encoding='utf-8') as f:
            json.dump(val_data, f, ensure_ascii=False, indent=4)

        # 產生 val_gt.json
        annotations = []
        for idx, row in enumerate(val_df.itertuples(index=False), start=1):
            annotations.append({
                'image_id': row.image_id,
                'id': idx,
                'caption': row.caption
            })
        images = []
        for row in val_df.itertuples(index=False):
            images.append({
                'id': row.image_id,
                'file_name': row.image
            })
        val_gt = {
            'annotations': annotations,
            'images': images
        }
        with open(os.path.join(self.output_dir, 'val_gt.json'), 'w', encoding='utf-8') as f:
            json.dump(val_gt, f, ensure_ascii=False, indent=4)
            
if __name__ == '__main__':
    # Example usage
    csv_path = 'filtered_encoder_data.csv'
    output_dir = 'generated_labels/caption'

    generator = CaptionGenerator(output_dir)
    generator.generate_captions(csv_path)
    print("Caption Json generated successfully.")
