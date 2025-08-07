import os
import json
import pandas as pd
import random
from tqdm import tqdm
from collections import defaultdict

ATTACK_SHOTS = ['smash', 'cross-court net shot', 'rush shot', 'drop net']
DEFEND_SHOTS = ['backstop', 'clear']
FLAT_SHOT = 'flat shot'

STRATEGIES = {
    "four_corner": {
        "type": "hit_area", "window_size": 4,
        "predicate": lambda hits: set(hits) == {"in the right backcourt", "in the left backcourt"},
        "element_predicate": None
    },
    "net_shot": {
        "type": "hit_area", "window_size": 2,
        "predicate": lambda hits: all(h in {"at the right side of the net", "at the left side of the net", "at the net"} for h in hits),
        "element_predicate": lambda h: h in {"at the right side of the net", "at the left side of the net", "at the net"}
    },
    "back_court": {
        "type": "hit_area", "window_size": 2,
        "predicate": lambda hits: all(h in {"in the right backcourt", "in the left backcourt"} for h in hits),
        "element_predicate": lambda h: h in {"in the right backcourt", "in the left backcourt"}
    },
    "flat_shot_sequence": {
        "type": "stroke_name", "window_size": 2,
        "predicate": lambda ss: all(s == FLAT_SHOT for s in ss),
        "element_predicate": lambda s: s == FLAT_SHOT
    },
    "counterattack": {
        "type": "counterattack", "window_size": 3,
        "predicate": None, "element_predicate": None
    }
}

STRATEGIES_TEMPLATE = {
    "four_corner": [
        "When does the players execute the four-corner pattern during a rally?",
        "Identify the timestamps where a corner-to-corner tactic occurs.",
        "At which points in the match do both backcourt corners get targeted in succession?"
    ],
    "net_shot": [
        "When do we see consecutive net-play exchanges in the rally?",
        "Locate moments of close-to-the-net shot sequences.",
        "At what times do players perform back-and-forth shots right at the net?"
    ],
    "back_court": [
        "When does a deep-court attack pattern appear?",
        "Pinpoint the instances of back-court rallies.",
        "At which moments are both rear-court zones hit consecutively?"
    ],
    "flat_shot_sequence": [
        "When do we observe a series of flat-drive strokes?",
        "Identify the moments of back-to-back flat-shot exchanges.",
        "At what points does a continuous flat-shot sequence unfold?"
    ],
    "upper_player_counter_attack": [
        "When does the upper player launch a counter-attack after a defensive shot?",
        "Identify moments where the upper player switches from defense to offense.",
        "At which timestamps does the upper player execute a defensive counterstrike?"
    ],
    "bottom_player_counter_attack": [
        "When does the bottom player initiate a counter-attack following a defensive return?",
        "Locate the points where the bottom player transitions from defense into an aggressive shot.",
        "At what moments does the bottom player perform a defensive riposte into attack?"
    ]
}
STRATEGIES_OBJECTIVE = {
    "four_corner": [
        "both backcourt corners are targeted in sequence",
        "players hit alternating shots to left and right backcourt corners",
        "the rally contains consecutive corner-to-corner movements",
        "both deep corners are attacked one after another"
    ],
    "net_shot": [
        "multiple shots are played close to the net",
        "players exchange hits right at the net area",
        "consecutive net shots occur in the rally",
        "shots are played near the net in succession"
    ],
    "back_court": [
        "multiple hits land in the backcourt area",
        "consecutive shots target the deep court",
        "players hit to the rear court in sequence",
        "back-to-back deep shots occur"
    ],
    "flat_shot_sequence": [
        "multiple flat shots are hit consecutively",
        "players execute a series of flat drive strokes",
        "consecutive flat shots occur without interruption",
        "a sequence of level driving shots takes place"
    ],
    "upper_player_counter_attack": [
        "the upper player transitions from defense shot(backstop, drop net) to attack shot(smash,cross-court net shot,rush shot,drop net) for counterattack"
    ],
    "bottom_player_counter_attack": [
        "the bottom player transitions from defense shot(backstop, drop net) to attack shot(smash,cross-court net shot,rush shot,drop net) for counterattack"
    ]
}

STROKE_TEMPLATE = {
    "player_stroke_area": [
        "When does the {player} hits a {stroke} {hit_area}?",
        "At what point in the rally does the {player} perform a {stroke} {hit_area}?",
        "Identify when the {player} executes a {stroke} {hit_area}.",
        "Locate the moment when a {stroke} {hit_area} is played by the {player}."
    ],
    "player_stroke": [
        "When does the {player} hits a {stroke}?",
        "At what time does the {player} execute a {stroke}?",
        "When in this rally does the {player} perform a {stroke}?",
        "Identify the moment the {player} plays a {stroke}."
    ],
    "stroke_only": [
        "When is a {stroke} hits?",
        "At what moment does a {stroke} occur?",
        "When during the rally does a {stroke} happen?",
        "Locate when the {stroke} takes place."
    ],
    "hit_area_only": [
        "Which stroke is hit {hit_area}?",
        "Which shot lands {hit_area}?",
        "Identify the stroke that occurs {hit_area}.",
        "What stroke happens {hit_area}?"
    ]
}
STROKE_OBJECTIVE = {
    "player_stroke_area": [
        "the particular player hits a stroke in a specific area",
        "the particular player executes a stroke at a particular location"
    ],
    "player_stroke": [
        "the particular player performs a specific stroke",
        "the particular player hits a particular stroke"
    ],
    "stroke_only": [
        "a specific stroke is hit",
        "a certain type of stroke occurs",
        "a particular stroke is executed"
    ],
    "hit_area_only": [
        "a stroke is hit in a specific area",
        "a stroke occurs in a particular location"
    ]
}


DEFEND_SET = set(DEFEND_SHOTS)
ATTACK_SET = set(ATTACK_SHOTS)
CHUNK_SIZE = 10


def split_dataset_by_field(
    json_path, train_path, val_path,
    val_to_train_ratio=0.05, seed=42
):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    train_data = [it for it in data if it.get('split')=='train']
    val_data   = [it for it in data if it.get('split')=='val']
    random.seed(seed)
    n_move = int(len(val_data)*val_to_train_ratio)
    moved = random.sample(val_data, n_move) if n_move>0 else []
    val_data = [it for it in val_data if it not in moved]
    train_data.extend(moved)
    for it in train_data: it.pop('split',None)
    for it in val_data:   it.pop('split',None)
    os.makedirs(os.path.dirname(train_path), exist_ok=True)
    os.makedirs(os.path.dirname(val_path), exist_ok=True)
    with open(train_path,'w',encoding='utf-8') as f:
        json.dump(train_data,f,ensure_ascii=False,indent=2)
    with open(val_path,'w',encoding='utf-8') as f:
        json.dump(val_data,f,ensure_ascii=False,indent=2)
    print(f"Split complete: Total {len(data)}, Train {len(train_data)}, Val {len(val_data)}")


class QAGenerator:
    def __init__(
        self,
        stroke_chunk_size=10,
    ):
        self.stroke_chunk_size  = stroke_chunk_size
        self.neg_ans_str        = "The event does not occur"
        self.question_id = 0
    def _make_cot_answer(self, thinking: list, answer_str, objective: str = "", required_info: list= []) -> str:
        prefix = "The event happens at "
        if answer_str == self.neg_ans_str:
            conclusion = "not occur"
        elif answer_str.startswith(prefix):
            conclusion = answer_str[len(prefix):]
        else:
            conclusion = answer_str.lower()
        focus_list = []
        if "player" in required_info:
            focus_list.append("player")
        if "stroke_name" in required_info:
            focus_list.append("stroke type")
        if "hit_area" in required_info:
            focus_list.append("hit area")
        focus_str = " and ".join(focus_list) if focus_list else ""
        lines = ["<thinking>"]
        if objective:
            lines.append(f"I need to identify when {objective}. Therefore, we focus on {focus_str}.")
        lines.extend(thinking)
        lines.append(f"therefore the answer is {conclusion}")
        lines.append("</thinking>")
        
        cot = "\n".join(lines) + f"\n<answer>{answer_str}</answer>"
        return cot
        
    def _generate_question(self, player, stroke, hit_area):
        template_keys = list(STROKE_TEMPLATE.keys())
        q_type = random.choice(template_keys)
        template = random.choice(STROKE_TEMPLATE[q_type])
        
        if q_type == "player_stroke_area":
            q = template.format(player=player, stroke=stroke, hit_area=hit_area)
        elif q_type == "player_stroke":
            q = template.format(player=player, stroke=stroke)
        elif q_type == "stroke_only":
            q = template.format(stroke=stroke)
        else:  # hit_area_only
            q = template.format(hit_area=hit_area)
        
        return " ".join(q.strip().split()), q_type

    def generate_by_rally(self,
                        csv_path: str,
                        output_path: str,
                        num_questions_per_rally: int = 5,
                        val_to_train_ratio: float = 0.05,
                        use_cot: bool = True):
        df = pd.read_csv(csv_path)
        player_vocab   = ["upper player", "bottom player"]
        stroke_vocab   = df['stroke_name'].unique().tolist()
        hit_area_vocab = df['hit_area'].dropna().unique().tolist()

        df['game']  = df['id'].apply(lambda x: x.split('_')[0])
        df['set']   = df['id'].apply(lambda x: x.split('_')[1])

        qa_dataset  = []

        for (game, set_, rally), group_df in tqdm(
                df.groupby(['game', 'set', 'rally']),
                desc="Generating QA by stroke-chunk"):

            group_df = group_df.reset_index(drop=True)

            for start in range(0, len(group_df), self.stroke_chunk_size):
                chunk_df = group_df.iloc[start:start + self.stroke_chunk_size]\
                                    .reset_index(drop=True)
                chunk_id    = f"{game}_{set_}_{rally}_chunk{start//self.stroke_chunk_size+1}"
                split_label = chunk_df['split'].iloc[0]
                chunk_files = chunk_df['id'].apply(lambda x: x + ".mp4").tolist()

                existing_triples = set(zip(chunk_df['player'],
                                        chunk_df['stroke_name'],
                                        chunk_df['hit_area']))
                existing_pairs   = set(zip(chunk_df['player'],
                                        chunk_df['stroke_name']))
                existing_strokes = set(chunk_df['stroke_name'])
                existing_areas   = set(chunk_df['hit_area'].dropna())

                all_triples = [(p, s, h)
                            for p in player_vocab
                            for s in stroke_vocab
                            for h in hit_area_vocab]
                all_pairs   = [(p, s) for p in player_vocab for s in stroke_vocab]

                neg_triples = [t for t in all_triples if t not in existing_triples]
                neg_pairs   = [p for p in all_pairs   if p not in existing_pairs]
                neg_strokes = [s for s in stroke_vocab   if s not in existing_strokes]
                neg_areas   = [h for h in hit_area_vocab if h not in existing_areas]

                neg_samples = [
                    (neg_triples, "player_stroke_area", STROKE_TEMPLATE["player_stroke_area"], lambda x: {"player": x[0], "stroke": x[1], "hit_area": x[2]}),
                    (neg_pairs,   "player_stroke",      STROKE_TEMPLATE["player_stroke"],      lambda x: {"player": x[0], "stroke": x[1]}),
                    (neg_strokes, "stroke_only",        STROKE_TEMPLATE["stroke_only"],        lambda x: {"stroke": x}),
                    (neg_areas,   "hit_area_only",      STROKE_TEMPLATE["hit_area_only"],      lambda x: {"hit_area": x})
                ]
                required_info_map = {
                    "player_stroke_area": ["player", "stroke_name", "hit_area"],
                    "player_stroke":      ["player", "stroke_name"],
                    "stroke_only":        ["stroke_name"],
                    "hit_area_only":      ["hit_area"]
                }

                for neg_pool, q_type, tmpl_pool, fmt in neg_samples:
                    if not neg_pool:
                        continue

                    sel = random.choice(neg_pool)
                    question = random.choice(tmpl_pool).format(**fmt(sel))
                    objective = random.choice(STROKE_OBJECTIVE[q_type])
                    required_info = required_info_map[q_type]
                    answer_str = self.neg_ans_str  

                    stroke_info = []
                    for idx, row in chunk_df.iterrows():
                        player = f"{row['player']} " if 'player' in required_info else ""
                        stroke = f"a {row['stroke_name']}" if 'stroke_name' in required_info else ""
                        hit_area = f"{row['hit_area']}" if 'hit_area' in required_info else ""
                        content = f"{player}hits {stroke}{(' ' + hit_area) if hit_area else ''}".strip()
                        stroke_info.append(content if content else "no data")
                    thinking = [f"stroke {i}: {info}" for i, info in enumerate(stroke_info)]

                    if use_cot:
                        cot = self._make_cot_answer(thinking, answer_str, objective, required_info)
                    else:
                        cot = answer_str

                    qa_dataset.append({
                        "question_id":   self.question_id,
                        "image":         chunk_files,
                        "question":      question,
                        "answer":        cot,
                        "question_type": q_type,
                        "is_impossible": True,
                        "chunk_id":      chunk_id,
                        "split":         split_label
                    })
                    self.question_id += 1

                # positive samples
                num_pos = num_questions_per_rally - len(neg_samples)
                sampled = chunk_df.sample(
                    n=num_pos,
                    replace=(len(chunk_df) < num_pos)
                )
                for _, row in sampled.iterrows():
                    question, q_type = self._generate_question(
                        row['player'], row['stroke_name'], row['hit_area']
                    )
                    objective = random.choice(STROKE_OBJECTIVE[q_type])
                    required_info = required_info_map[q_type]

                    mask = None
                    if q_type == "player_stroke_area":
                        mask = (
                            (chunk_df['player'] == row['player']) &
                            (chunk_df['stroke_name'] == row['stroke_name']) &
                            (chunk_df['hit_area'] == row['hit_area'])
                        )
                    elif q_type == "player_stroke":
                        mask = (
                            (chunk_df['player'] == row['player']) &
                            (chunk_df['stroke_name'] == row['stroke_name'])
                        )
                    elif q_type == "stroke_only":
                        mask = (chunk_df['stroke_name'] == row['stroke_name'])
                    else:  # hit_area_only
                        mask = (chunk_df['hit_area'] == row['hit_area'])
                    idxs = chunk_df[mask].index.tolist()
                    idx_str = ",".join(str(i) for i in idxs)
                    answer_str = (
                        f"The event happens at stroke {idx_str}"
                        if len(idxs) == 1
                        else f"The event happens at strokes {idx_str}"
                    )

                    stroke_info = []
                    for idx2, row_data in chunk_df.iterrows():
                        player = f"{row_data['player']} " if 'player' in required_info else ""
                        stroke = f"a {row_data['stroke_name']}" if 'stroke_name' in required_info else ""
                        hit_area = f"{row_data['hit_area']}" if 'hit_area' in required_info else ""
                        content = f"{player}hits {stroke}{(' ' + hit_area) if hit_area else ''}".strip()
                        stroke_info.append(content if content else "no data")
                    thinking = [f"stroke {i}: {info}" for i, info in enumerate(stroke_info)]

                    if use_cot:
                        cot = self._make_cot_answer(thinking, answer_str, objective, required_info)
                    else:
                        cot = answer_str

                    qa_dataset.append({
                        "question_id":   self.question_id,
                        "image":         chunk_files,
                        "question":      question,
                        "answer":        cot,
                        "question_type": q_type,
                        "is_impossible": False,
                        "chunk_id":      chunk_id,
                        "split":         split_label
                    })
                    self.question_id += 1
        return qa_dataset

    def _detect_strategies(self, df):
        raw = []
        df['game'] = df['id'].str.split('_', n=2).str[0]
        df['set']  = df['id'].str.split('_', n=2).str[1]
        for _, g in df.groupby(['game','set','rally','split']):
            hits, strokes = g['hit_area'].tolist(), g['stroke_name'].tolist()
            players, ids_seq = g['player'].tolist(), g['id'].tolist()
            L = len(g)
            if L<2: continue
            game,set_,rally,split = g.iloc[0][['game','set','rally','split']]
            # 一般策略
            for name,cfg in STRATEGIES.items():
                if cfg['type']=='counterattack': continue
                ws, seq = cfg['window_size'], hits if cfg['type']=='hit_area' else strokes
                elem = cfg['element_predicate']
                i=0
                while i<=L-ws:
                    win = seq[i:i+ws]
                    if not cfg['predicate'](win):
                        i+=1; continue
                    start,end=i,i+ws-1
                    if elem:
                        j=end+1
                        while j<L and elem(seq[j]): end,j=j,j+1
                        i=j
                    else:
                        i+=1
                    ids = ids_seq[start:end+1]
                    raw.append({'game':game,'set':set_,'rally':rally,'split':split,'strategy':name,'ids':ids})
            # counterattack
            ws = STRATEGIES['counterattack']['window_size']
            if L>=ws:
                for i in range(L-ws+1):
                    if strokes[i] in DEFEND_SET and strokes[i+2] in ATTACK_SET and players[i]==players[i+2]:
                        side=players[i]
                        sn = 'upper_player_counter_attack' if side=='upper player' else 'bottom_player_counter_attack'
                        raw.append({'game':game,'set':set_,'rally':rally,'split':split,'strategy':sn,'ids':ids_seq[i:i+ws]})
        return raw

    def _merge_segments(self, raw, df):
        merged=[]; groups=defaultdict(list)
        for d in raw:
            key=(d['game'],d['set'],d['rally'],d['split'],d['strategy'])
            groups[key].append(d['ids'])
        for key, lists in groups.items():
            game,set_,rally,split,strat = key
            full = df[(df['game']==game)&(df['set']==set_)&(df['rally']==rally)&(df['split']==split)]['id'].tolist()
            pos = {id:i for i,id in enumerate(full)}
            segs = sorted(lists, key=lambda x: pos[x[0]])
            cur = []
            for s in segs:
                if not cur:
                    cur = s.copy()
                else:
                    # 如果 s[0] 在 cur 的最後一個位置之「之前或重疊」
                    if pos[s[0]] <= pos[cur[-1]]:
                        # 取聯集並重排序
                        cur = sorted(set(cur) | set(s), key=lambda id: pos[id])
                    else:
                        # 沒有重疊，先處理上一段
                        merged.extend(self._process_segment(game,set_,rally,split,strat,cur,full,pos))
                        cur = s.copy()
            # 處理最後一段
            if cur:
                merged.extend(self._process_segment(game,set_,rally,split,strat,cur,full,pos))
        return merged

    def _process_segment(self, game, set_, rally, split, strat, seg_ids, full, pos):
        rec=[]; L=len(seg_ids)
        if L>=CHUNK_SIZE:
            for i in range(0,L,CHUNK_SIZE):
                c=seg_ids[i:i+CHUNK_SIZE]
                rec.append({'game':game,'set':set_,'rally':rally,'split':split,'strategy':strat,'image':c,'ans':c})
        else:
            post=min(L,CHUNK_SIZE-L); pre=CHUNK_SIZE-L-post
            st,ed=pos[seg_ids[0]],pos[seg_ids[-1]]
            pre_ids=full[max(0,st-pre):st]
            post_ids=full[ed+1:ed+1+post]
            ids=pre_ids+seg_ids+post_ids
            rec.append({'game':game,'set':set_,'rally':rally,'split':split,'strategy':strat,'image':ids,'ans':seg_ids})
        return rec

    def _compute_ans_idx(self, row):
        return [row['image'].index(a) for a in row['ans']]

    def generate_tactical_qa(self,csv_path,output_path,val_to_train_ratio=0.05):
        df=pd.read_csv(csv_path,encoding='utf-8')
        raw=self._detect_strategies(df)
        merged=self._merge_segments(raw,df)
        mdf=pd.DataFrame(merged)
        mdf['ans_idx']=mdf.apply(self._compute_ans_idx,axis=1)
        qa_dataset=[]; 
        for _,grp in tqdm(mdf.groupby(['game','set','rally']),desc="Tactical QA"):
            for _,row_data in grp.iterrows():
                # positive sample
                tpl=STRATEGIES_TEMPLATE.get(row_data['strategy'],[f"When does the {row_data['strategy']} occur?"])
                objective_list=STRATEGIES_OBJECTIVE.get(row_data['strategy'],[""])
                question=random.choice(tpl)
                objective=random.choice(objective_list) if objective_list and objective_list[0] else ""
                if row_data['strategy']=='upper_player_counter_attack' or row_data['strategy']=='bottom_player_counter_attack':
                    required_info = ['player','stroke_name']
                else:
                    required_info = [STRATEGIES[row_data['strategy']]['type']]
                ans_indices=row_data['ans_idx']
                ans_str=','.join(str(i) for i in ans_indices)
                thinking = []
                chunk_files = [img + '.mp4' for img in row_data['image']]
                
                stroke_info = []
                for img in row_data['image']:
                    stroke_row = df[df['id'] == img]
                    if not stroke_row.empty:
                        stroke_data = stroke_row.iloc[0]
                        if 'player' in required_info:
                            player = f"{stroke_data['player']} "
                        else:
                            player = ""
                        if 'stroke_name' in required_info:
                            stroke_name = f" a {stroke_data['stroke_name']}"
                        else:
                            stroke_name = ""    
                        if 'hit_area' in required_info:
                            hit_area = f" {stroke_data['hit_area']}"
                        else:
                            hit_area = ""

                        stroke_info.append(f"{player}hits{stroke_name}{hit_area}")
                    else:
                        stroke_info.append("no data")
                
                for idx, info in enumerate(stroke_info):
                    thinking.append(f"stroke {idx}: {info}")
                if len(ans_indices)==1:
                    answer_str=f"The event happens at stroke {ans_str}"
                else:
                    answer_str=f"The event happens at strokes {ans_str}"
                cot=self._make_cot_answer(thinking,answer_str,objective,required_info)
                qa_dataset.append({
                    'question_id':self.question_id,
                    'image':chunk_files,
                    'question':question,
                    'answer':cot,
                    'question_type':row_data['strategy'],
                    'is_impossible': False,
                    'split':row_data['split']
                })
                self.question_id+=1
                # negative sample
                other_strats = [s for s in STRATEGIES_TEMPLATE.keys() if s != row_data['strategy']]
                neg_strategy = random.choice(other_strats)
                neg_tpl = STRATEGIES_TEMPLATE.get(neg_strategy, [f"When does the {neg_strategy} occur?"])
                neg_objective_list = STRATEGIES_OBJECTIVE.get(neg_strategy, [""])
                neg_question = random.choice(neg_tpl)
                neg_objective = random.choice(neg_objective_list) if neg_objective_list and neg_objective_list[0] else ""
                neg_answer_str = self.neg_ans_str
                if neg_strategy=='upper_player_counter_attack' or neg_strategy=='bottom_player_counter_attack':
                    required_info = ['player','stroke_name']
                else:
                    required_info = [STRATEGIES[neg_strategy]['type']]
                thinking = []
                
                # Get stroke info from dataframe based on image ids
                stroke_info = []
                for img in row_data['image']:
                    stroke_row = df[df['id'] == img]
                    if not stroke_row.empty:
                        stroke_data = stroke_row.iloc[0]
                        if 'player' in required_info:
                            player = f"{stroke_data['player']} "
                        else:
                            player = ""
                        if 'stroke_name' in required_info:
                            stroke_name = f" a {stroke_data['stroke_name']}"
                        else:
                            stroke_name = ""    
                        if 'hit_area' in required_info:
                            hit_area = f" {stroke_data['hit_area']}"
                        else:
                            hit_area = ""

                        stroke_info.append(f"{player}hits{stroke_name}{hit_area}")
                    else:
                        stroke_info.append("no data")
                
                for idx, info in enumerate(stroke_info):
                    thinking.append(f"stroke {idx}: {info}")
                neg_cot = self._make_cot_answer(thinking, neg_answer_str, neg_objective, required_info)
                
                qa_dataset.append({
                    'question_id': self.question_id,
                    'image': chunk_files,
                    'question': neg_question,
                    'answer': neg_cot,
                    'question_type': neg_strategy, 
                    'is_impossible': True,
                    'split': row_data['split']
                })
                self.question_id += 1
        return qa_dataset

if __name__=='__main__':
    gen = QAGenerator(
        stroke_chunk_size=10
        )
    tactical_qa = gen.generate_tactical_qa(
        'data_processing/processed/filtered_encoder_data.csv',
        'generated_labels/tactical_qa.json'
    )
    stroke_qa_by_rally = gen.generate_by_rally(
        csv_path='data_processing/processed/filtered_encoder_data.csv',
        output_path='generated_labels/stroke_qa_by_rally.json',
        num_questions_per_rally=14,
        val_to_train_ratio=0.05,
        use_cot=True
    )
    qa_dataset = tactical_qa + stroke_qa_by_rally
    output_path = 'generated_labels/QA_strategy/QA_strategy.json'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(qa_dataset, f, ensure_ascii=False, indent=2)
    
    train_path = os.path.join(os.path.dirname(output_path), 'train.json')
    val_path   = os.path.join(os.path.dirname(output_path), 'val.json')
    split_dataset_by_field(output_path, train_path, val_path, val_to_train_ratio=0.05)

    print(f"Saved {len(qa_dataset)} questions to {output_path}")
    print("Stroke QA generation completed.")
