import os
import pandas as pd
from tqdm import tqdm

class CaptionGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_captions(self, csv_path: str):
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
        return pd.DataFrame(captions)

if __name__ == '__main__':
    # Example usage
    csv_path = 'filtered_encoder_data.csv'
    output_dir = 'generated_labels'

    generator = CaptionGenerator(output_dir)
    caption_df = generator.generate_captions(csv_path)
    caption_df.to_csv(os.path.join(output_dir, 'tmp_dataset_labels_caption.csv'), index=False)
    print("Caption CSV generated successfully.")
