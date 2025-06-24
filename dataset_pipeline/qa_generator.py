import os
import json
import pandas as pd
import random
from tqdm import tqdm
def split_dataset_by_field(
    json_path,
    train_path,
    val_path,
    val_to_train_ratio = 0.05,
    seed = 42
) -> None:
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    train_data = [item for item in data if item.get('split') == 'train']
    val_data   = [item for item in data if item.get('split') == 'val']

    random.seed(seed)
    n_move = int(len(val_data) * val_to_train_ratio)
    if n_move > 0 and val_data:
        moved = random.sample(val_data, n_move)
        val_data = [item for item in val_data if item not in moved]
        train_data.extend(moved)

    for item in train_data:
        item.pop('split', None)
    for item in val_data:
        item.pop('split', None)

    os.makedirs(os.path.dirname(train_path), exist_ok=True)
    os.makedirs(os.path.dirname(val_path), exist_ok=True)

    with open(train_path, 'w', encoding='utf-8') as f:
        json.dump(train_data, f, ensure_ascii=False, indent=2)
    with open(val_path, 'w', encoding='utf-8') as f:
        json.dump(val_data, f, ensure_ascii=False, indent=2)

    print(f"Split complete: Total {len(data)}, Train {len(train_data)}, Val {len(val_data)}, Moved {n_move}")


class QAGenerator:
    def __init__(self,
                 templates_with_all,
                 templates_player_stroke,
                 templates_stroke_only,
                 templates_hit_area_only,
                 stroke_chunk_size=5,
                 caption_csv_path="generated_labels/caption/dataset_labels_caption.csv"):
        self.templates_with_all       = templates_with_all
        self.templates_player_stroke  = templates_player_stroke
        self.templates_stroke_only    = templates_stroke_only
        self.templates_hit_area_only  = templates_hit_area_only
        self.all_templates = (
            templates_with_all +
            templates_player_stroke +
            templates_stroke_only +
            templates_hit_area_only
        )
        self.stroke_chunk_size = stroke_chunk_size
        self.neg_ans_str = "The event does not occur"
        if caption_csv_path is None:
            raise ValueError("請提供 caption_csv_path或先執行 caption_generator.py 生成 caption CSV 檔")
        df_caps = pd.read_csv(caption_csv_path, encoding='utf-8')
        self.caption_dict = dict(zip(df_caps['image_id'], df_caps['caption']))
    def make_cot_answer(self, thinking: list, answer_str) -> str:
        prefix = "The event happens at "
        if answer_str == self.neg_ans_str:
            conclusion = "not occur"
        elif answer_str.startswith(prefix):
            conclusion = answer_str[len(prefix):]
        else:
            conclusion = answer_str.lower()
        lines = ["<thinking>"] + thinking + [f"therefore the answer is {conclusion}", "</thinking>"]
        cot = "\n".join(lines) + f"\n<answer>{answer_str}</answer>"
        return cot
        
    def generate_question(self, player, stroke, hit_area):
        template = random.choice(self.all_templates)
        if template in self.templates_with_all:
            q = template.format(player=player, stroke=stroke, hit_area=hit_area)
            q_type = "player_stroke_area"
        elif template in self.templates_player_stroke:
            q = template.format(player=player, stroke=stroke)
            q_type = "player_stroke"
        elif template in self.templates_stroke_only:
            q = template.format(stroke=stroke)
            q_type = "stroke_only"
        else:
            q = template.format(hit_area=hit_area)
            q_type = "hit_area_only"
        return " ".join(q.strip().split()), q_type

    def generate_by_rally(self,
                                  csv_path,
                                  output_path,
                                  num_questions_per_rally=5,
                                  val_to_train_ratio= 0.05,
                                  use_cot: bool = True
):
        df = pd.read_csv(csv_path)

        player_vocab   = ["upper player", "bottom player"]
        stroke_vocab   = df['stroke_name'].unique().tolist()
        hit_area_vocab = df['hit_area'].dropna().unique().tolist()

        df['game']   = df['id'].apply(lambda x: x.split('_')[0])
        df['set']    = df['id'].apply(lambda x: x.split('_')[1])
        df['rally']  = df['rally']

        qa_dataset = []
        question_id = 0  # initialize question counter

        for (game, set_, rally), group_df in tqdm(
                df.groupby(['game', 'set', 'rally']),
                desc="Generating QA by stroke-chunk"):

            group_df = group_df.reset_index(drop=True)

            for start in range(0, len(group_df), self.stroke_chunk_size):
                chunk_df = group_df.iloc[start:start + self.stroke_chunk_size]\
                                     .reset_index(drop=True)
                chunk_id = f"{game}_{set_}_{rally}_chunk{start//self.stroke_chunk_size+1}"
                split_label = chunk_df['split'].iloc[0]
                chunk_filenames = chunk_df['id'].apply(lambda x: x + ".mp4").tolist()
                thinking = []
                for idx, row in chunk_df.iterrows():
                    img_id = row['id']  # e.g. "game33_set3_128437"
                    caption = self.caption_dict.get(img_id, "no caption")
                    thinking.append(f"stroke {idx}: {caption}")
                existing_triples = set(zip(chunk_df['player'],
                                           chunk_df['stroke_name'],
                                           chunk_df['hit_area']))
                all_triples = [(p, s, h)
                               for p in player_vocab
                               for s in stroke_vocab
                               for h in hit_area_vocab]
                neg_triples = [c for c in all_triples
                               if c not in existing_triples]

                existing_pairs = set(zip(chunk_df['player'],
                                         chunk_df['stroke_name']))
                all_pairs = [(p, s) for p in player_vocab
                             for s in stroke_vocab]
                neg_pairs   = [c for c in all_pairs
                               if c not in existing_pairs]

                existing_strokes = set(chunk_df['stroke_name'])
                neg_strokes = [s for s in stroke_vocab
                               if s not in existing_strokes]

                existing_areas = set(chunk_df['hit_area'].dropna())
                neg_areas = [h for h in hit_area_vocab
                             if h not in existing_areas]

                neg_samples = [
                    (neg_triples, self.templates_with_all, lambda x: {"player": x[0], "stroke": x[1], "hit_area": x[2]}),
                    (neg_pairs, self.templates_player_stroke, lambda x: {"player": x[0], "stroke": x[1]}),
                    (neg_strokes, self.templates_stroke_only, lambda x: {"stroke": x}),
                    (neg_areas, self.templates_hit_area_only, lambda x: {"hit_area": x})
                ]
                
                for neg_pool, template_pool, format_func in neg_samples:
                    if neg_pool:
                        selected = random.choice(neg_pool)
                        tmpl = random.choice(template_pool)
                        q = tmpl.format(**format_func(selected))
                        answer_str    = self.neg_ans_str
                        cot_full = self.make_cot_answer(thinking, self.neg_ans_str)
                        qa_dataset.append({
                            "question_id":   question_id,
                            "image":         chunk_filenames,
                            "question":      q,
                            # "thinking":      thinking,
                            "answer":        cot_full if use_cot else answer_str,
                            # "coT_answer":    cot_full,
                            "is_impossible": True,
                            "chunk_id":      chunk_id,
                            "split":         split_label

                        })
                        question_id += 1

                num_pos = num_questions_per_rally - 4
                sampled = chunk_df.sample(
                    n=num_pos,
                    replace=(len(chunk_df) < num_pos)
                )
                for _, row in sampled.iterrows():
                    player, stroke, hit_area = (
                        row['player'],
                        row['stroke_name'],
                        row['hit_area']
                    )
                    q, q_type = self.generate_question(player, stroke, hit_area)

                    if q_type == "player_stroke_area":
                        mask = (
                            (chunk_df['player'] == player) &
                            (chunk_df['stroke_name'] == stroke) &
                            (chunk_df['hit_area'] == hit_area)
                        )
                    elif q_type == "player_stroke":
                        mask = (
                            (chunk_df['player'] == player) &
                            (chunk_df['stroke_name'] == stroke)
                        )
                    elif q_type == "stroke_only":
                        mask = (chunk_df['stroke_name'] == stroke)
                    else:  # hit_area_only
                        mask = (chunk_df['hit_area'] == hit_area)

                    indices = chunk_df[mask].index.tolist()
                    index_answer = ",".join(str(i) for i in indices)
                    if len(indices) == 1:
                        answer_str = f"The event happens at stroke {index_answer}"
                    else:
                        answer_str = f"The event happens at strokes {index_answer}"
                    cot_full = self.make_cot_answer(thinking, answer_str)

                    qa_dataset.append({
                        "question_id":   question_id,
                        "image":         chunk_filenames,
                        "question":      q,
                        # "thinking":      thinking,
                        "answer":        cot_full if use_cot else answer_str,
                        # "coT_answer":    cot_full,
                        "is_impossible": False,
                        "chunk_id":      chunk_id,
                        "split":         split_label
                    })
                    question_id += 1

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(qa_dataset, f, ensure_ascii=False, indent=2, default=str)

        train_path = os.path.join(os.path.dirname(output_path), 'train.json')
        val_path   = os.path.join(os.path.dirname(output_path), 'val.json')
        split_dataset_by_field(output_path, train_path, val_path, val_to_train_ratio)

if __name__ == '__main__':
    # Example usage
    templates_all = ["When does the {player} hits a {stroke} {hit_area}?" ]
    templates_ps = ["When does the {player} hits a {stroke}?" ]
    templates_s = ["When is a {stroke} hits?" ]
    templates_h = ["Which stroke is hit {hit_area}?" ]

    gen = QAGenerator(
        templates_all, templates_ps, templates_s, templates_h,
        stroke_chunk_size=5,
        caption_csv_path='generated_labels/caption/dataset_labels_caption.csv'
    )
    gen.generate_by_rally(
        csv_path='data_processing/processed/filtered_encoder_data.csv',
        output_path='generated_labels/QA/qa_dataset.json',
        num_questions_per_rally=14,
        val_to_train_ratio=0.05

    )
