import pandas as pd

def filter_and_dedup_encoder_data(
    encoder_csv_path,
    stroke_map_ty_path,
    hit_area_map_path,
    stroke_map_llm_path,
    output_csv_path,
    dedup_keep = 'last',
    sort_by = None
) -> None:

    stroke_mapping_df = pd.read_csv(stroke_map_ty_path)
    valid_strokes = stroke_mapping_df['Stroke'].tolist()

    df = pd.read_csv(encoder_csv_path)
    df = df[df['type'].isin(valid_strokes)].copy()

    df = df[['id', 'upper', 'type', 'backhand', 'relabel_hit_area','split',"rally"]]

    df['backhand'] = df['backhand'].apply(lambda x: 1 if x == 1 else 0)
    df['player']   = df['upper'].apply(lambda x: 'upper player' if x == 1 else 'bottom player')

    df['relabel_hit_area'] = pd.to_numeric(df['relabel_hit_area'], errors='coerce')
    df.dropna(subset=['relabel_hit_area'], inplace=True)

    hit_area_df = pd.read_csv(hit_area_map_path)
    hit_area_dict = hit_area_df.set_index('id')['hit_area'].to_dict()
    df['hit_area'] = df['relabel_hit_area'].astype(int).map(hit_area_dict)

    df['stroke_name'] = df['type'].map(
        stroke_mapping_df.set_index('Stroke')['English_Type']
    ).str.lower()

    stroke_map_llm_df = pd.read_csv(stroke_map_llm_path)
    df['stroke_LLM'] = df['type'].map(
        stroke_map_llm_df.set_index('Stroke')['English_Type']
    )

    df.drop(columns=['upper'], inplace=True)

    if sort_by:
        df.sort_values(by=sort_by, inplace=True)
    else:
        df.sort_index(inplace=True)
    df.drop_duplicates(subset='id', keep=dedup_keep, inplace=True)

    df.to_csv(output_csv_path, index=False)
    print(f"done {output_csv_path}")
if __name__ == '__main__':
    filter_and_dedup_encoder_data(
        encoder_csv_path='data_processing/raw/encoder_data.csv',
        stroke_map_ty_path='data_processing/mapping/stroke_mapping_name.csv',
        hit_area_map_path='data_processing/mapping/hit_area_mapping.csv',
        stroke_map_llm_path='data_processing/mapping/stroke_mapping_llm.csv',
        output_csv_path='data_processing/processed/filtered_encoder_data.csv',
        dedup_keep='last',       
        sort_by=None             
    )
