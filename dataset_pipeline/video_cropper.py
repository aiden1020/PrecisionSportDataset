import os
import cv2
import pandas as pd
from tqdm import tqdm

class VideoCropper:
    def __init__(self, output_path: str, video_dir: str = 'Dataset/Video'):
        self.video_dir = video_dir
        self.output_path = output_path
        os.makedirs(self.output_path, exist_ok=True)

    def _crop_video(self, video_path: str, start_frame: int, end_frame: int, output_path: str, fps: float):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Cannot open video: {video_path}")

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        frame = start_frame
        while frame <= end_frame:
            ret, img = cap.read()
            if not ret:
                break
            writer.write(img)
            frame += 1

        writer.release()
        cap.release()

    def crop_videos(self, csv_path: str):
        df = pd.read_csv(csv_path)
        for _, row in tqdm(df.iterrows(), total=len(df), desc='Cropping videos'):
            frame_num = int(row['id'].split('_')[-1])
            game = row['id'].split('_')[0]
            video_file = os.path.join(self.video_dir, f"{game}.mp4")
            start_frame, end_frame = frame_num - 7, frame_num + 8
            out_name = f"{row['id']}.mp4"
            out_path = os.path.join(self.output_path, out_name)

            cap = cv2.VideoCapture(video_file)
            fps = cap.get(cv2.CAP_PROP_FPS)
            cap.release()

            self._crop_video(video_file, start_frame, end_frame, out_path, fps)

if __name__ == '__main__':
    # Example usage
    cropper = VideoCropper(output_path='Output',video_dir='Dataset/Video')
    cropper.crop_videos('filtered_encoder_data.csv')

