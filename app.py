import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
from janome.tokenizer import Tokenizer
import os
import datetime
import re

# データディレクトリのパス
DATA_DIR = "voiceboxapp3/data"

def count_data_in_range(date_range, dataframes):
    today = datetime.date.today()
    if date_range == "当月":
        start_date = today.replace(day=1)
        end_date = today
    elif date_range == "前月":
        first_day_of_previous_month = today.replace(day=1) - datetime.timedelta(days=1)
        start_date = first_day_of_previous_month.replace(day=1)
        end_date = first_day_of_previous_month
    elif date_range == "3ヶ月":
        start_date = today - datetime.timedelta(days=90)
        end_date = today
    elif date_range == "6ヶ月":
        start_date = today - datetime.timedelta(days=180)
        end_date = today
    elif date_range == "今年":
        start_date = today.replace(month=1, day=1)
        end_date = today
    elif date_range == "去年":
        start_date = today.replace(year=today.year - 1, month=1, day=1)
        end_date = today.replace(year=today.year - 1, month=12, day=31)
    else:
        # 全ての期間を選択した場合、フィルタリングせずに全てのデータフレームを結合
        combined_df = pd.concat(dataframes, ignore_index=True)
        return "全て (" + str(len(combined_df)) + ")", combined_df # データフレームも返す

    filtered_dataframes = []
    count = 0
    for df in dataframes:
        df['受付日時'] = pd.to_datetime(df['受付日時'], errors='coerce')
        filtered_df_temp = df[(df['受付日時'].dt.date >= start_date) & (df['受付日時'].dt.date <= end_date)]
        filtered_dataframes.append(filtered_df_temp)
        count += len(filtered_df_temp)
    # フィルタリングされたデータフレームを結合
    combined_df = pd.concat(filtered_dataframes, ignore_index=True)
    return date_range + " (" + str(count) + ")", combined_df # データフレームも返す

def create_wordcloud(word_counts, filename):
    '''
    単語の出現頻度からワードクラウドを作成し、指定されたファイル名で保存する。
    '''
    try:
        wordcloud = WordCloud(
            font_path="voiceboxapp3/fonts/NotoSansJP-Regular.ttf", # 日本語フォント
            width=800,
            height=400,
            background_color="white",
            colormap="viridis",
            collocations=False, # 連語を考慮しない
            prefer_horizontal=1.0 # 横書きのみにする
        ).generate_from_frequencies({word[0]: count for word, count in word_counts.items()})
        wordcloud.to_file(filename)
    except Exception as e:
        st.error(f"ワードクラウドの作成に失敗しました: {e}")
        return False
    return True

def analyze_text(text, store_names, exclude_words):
    '''
    テキストを形態素解析して、単語の出現頻度をカウントする。
    '''
    t = Tokenizer()
    tokens = t.tokenize(text)
    stop_words = ['http', 'https', '会員', '店舗', '利用', 'お願い', 'ヶ月', '弊社', '世話', 'プログラム', 'スタッフ', '入電', 'ホリデイ', '時間', '対応', '店長', '今回', '大変', 'スポーツ', 'メディア', '使用', '連絡', '従業', '匿名', 'to', 'sho', 'net', 'info', '電話,', '宛先', '方々', '運営', '正直', '会社', '案内', '株式会社', '多く', '営業', '希望', '説明', '今後', '担当', '場合', '現在', 'お世話', 'こちら', '自分', '以上', '社員', '内容', 'ホリデー', 'クラブ', '今日', '毎日', '宜しく', '御社', '失礼', '直接', 'その後', '貴社', '予定', '設定', '本社', '本部', 'メール', 'だらけ', 'ホリデイスポーツクラブ', '番号', '先日', '方法', '仕方', '提供', '毎回', '以外', '全て', 'jp', '問い合わせ', '欲しい', 'ほしい', 'ところ', '事業', '状況', '指摘,', '意見', '同士', '行為', '返答', '投稿', '相談', '是非', '開催', '一部', '難しい', '関係', '最近', '上記', '通り', '周り', 'Fi', '回答', '問題', '要望', 'みんな', '返信', '本日', '皆さん', 'com', '早急', '以前', '週間', 'お客様', '仕事', '情報', '平日', 'Wi', 'トレ', '今月', '確認', 'インストラクター', '意味', '一緒', '状態', '実施', '特定', 'みたい', '責任', '現状', '可能', '部分', '先生', '程度', 'フリー', '企業', '昨日', '制限', '契約', '申し訳', '紀文', '管理', 'お伝え', '提案', '質問', '感じ', '自身', '非常', '経営', 'なかっ', '商品', '経営', '理由', 'たくさん', '施設', '以降', '喚起', '導入', '個人', '全体', '特別', '以下', 'いかが']
    exclude_words = []
    if store_names:
        exclude_words = [s.replace("店", "") for s in store_names if isinstance(s, str)]
    word_data = [(token.surface, token.part_of_speech.split(',')[0]) for token in tokens if token.part_of_speech.split(',')[0] in ['名詞', '形容詞'] and len(token.surface) > 1 and not (len(token.surface) == 2 and all(ord(c) >= 0x3040 and ord(c) <= 0x309F for c in token.surface)) and token.surface.isalnum() and not token.surface.isdigit() and token.surface not in stop_words and '@' not in token.surface and '.' not in token.surface and token.surface not in exclude_words and not re.search(r'[\U0001f600-\U0001f64f\U0001f300-\U0001f5ff\U0001f680-\U0001f6ff\U0001f1e0-\U0001f1ff]+', token.surface)]
    return Counter(word_data)

def main():
    st.title("お客様の声分析アプリ")

    # データディレクトリ内のCSVファイルのリストを取得
    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]

    if not csv_files:
        st.error("データディレクトリにCSVファイルが見つかりませんでした。")
        return
    
    # データフレームを格納するリスト
    dataframes = []
    for csv_file in csv_files:
        file_path = os.path.join(DATA_DIR, csv_file)
        try:
            df = pd.read_csv(file_path, encoding="cp932")
            dataframes.append(df)
            # デバッグ: 各データフレームのレコード数を出力
            print(f"{csv_file} のレコード数: {len(df)}")
        except Exception as e:
            st.error(f"ファイル {csv_file} の読み込みに失敗しました: {e}")
            return

    # 日付絞り込みの選択肢
    date_options_with_df = [count_data_in_range(option, dataframes) for option in ["当月", "前月", "3ヶ月", "6ヶ月", "今年", "去年", "全て"]]
    # 選択肢の文字列のみを抽出
    date_options = [option[0] for option in date_options_with_df]
    selected_date_range = st.selectbox("日付で絞り込む", date_options, index=0)

    # 選択された期間に基づいてデータフレームをフィルタリング
    # 選択された日付範囲に対応するデータフレームを取得
    filtered_df = next(df for date_str, df in date_options_with_df if date_str == selected_date_range)

    # エリアのリストを取得
    area_counts = {}
    for index, row in filtered_df.iterrows():
        area_name = row.get("店舗を選択してください。", None) # エリアの列名を修正
        if area_name:
            if area_name not in area_counts:
                area_counts[area_name] = 0
            area_counts[area_name] += 1

    area_names = list(set(area_counts.keys()))

    # エリアの選択肢をレコード数の多い順にソート
    sorted_area_names = sorted(area_counts.items(), key=lambda x: x[1], reverse=True)
    area_names_with_counts = [f"{name} ({count})" for name, count in sorted_area_names]
    area_names = [name for name, count in sorted_area_names]

    # エリアで絞り込むためのセレクトボックス
    selected_area = st.selectbox("エリアを選択してください", ["全て"] + area_names_with_counts)

    # 店舗名を出現回数が多い順にソート
    store_counts = {}
    if selected_area != "全て":
        selected_area_name = selected_area.split('(')[0].strip()
        df_area_filtered = filtered_df[filtered_df["店舗を選択してください。"] == selected_area_name]
        print(f"df_area_filtered (エリアで絞り込み後) のレコード数: {len(df_area_filtered)}")
    else:
        df_area_filtered = filtered_df  # selected_areaが"全て"の場合にもdf_filteredを定義
        print(f"df_area_filtered (エリアで絞り込み後) のレコード数: {len(df_area_filtered)}")
    for store_name in df_area_filtered["子要素"].unique().tolist():
        if store_name not in store_counts:
            store_counts[store_name] = 0
        # df_filteredに対して集計
        store_counts[store_name] += len(df_area_filtered[df_area_filtered["子要素"] == store_name])

    sorted_store_names = sorted(store_counts.items(), key=lambda x: x[1], reverse=True)
    store_names_with_counts = [f"{name} ({count})" for name, count in sorted_store_names]
    store_names = [name for name, count in sorted_store_names]

    # 店舗名で絞り込むためのセレクトボックス
    selected_store = st.selectbox("店舗名を選択してください", ["全て"] + store_names_with_counts)

    # 除外する店舗名のリストを作成
    exclude_words = [s.replace("店", "") for s in store_names if isinstance(s, str)]

    # 選択された店舗のデータのみを抽出
    all_text_data = ""
    sentence_data = []

    if selected_area != "全て":
        selected_area_name = selected_area.split('(')[0].strip()
        df_area_filtered = filtered_df[filtered_df["店舗を選択してください。"] == selected_area_name]
    else:
        df_area_filtered = filtered_df

    if selected_store != "全て":
        selected_store_name = selected_store.split('(')[0].strip()
        df_store_filtered = df_area_filtered[df_area_filtered["子要素"] == selected_store_name]
        print(f"df_store_filtered (店舗名で絞り込み後) のレコード数: {len(df_store_filtered)}")
    else:
        df_store_filtered = df_area_filtered
        print(f"df_store_filtered (店舗名で絞り込み後) のレコード数: {len(df_store_filtered)}")

    try:
        for index, row in df_store_filtered.iterrows():
            all_text_data += row["内容"] + " "
            sentence_data.append({"受付日時": row.get("受付日時", "不明"), "内容": row["内容"], "子要素": row["子要素"]})
        word_counts = analyze_text(all_text_data, store_names, exclude_words)
    except KeyError:
        st.error("CSVファイルに'内容'という列が存在しません。'内容'列が存在するか確認してください。")
        return
    
    # テキストデータを分析
    total_words = sum(word_counts.values())
    most_common_words = word_counts.most_common(100)

    # ワードクラウドを作成
    wordcloud_filename = "all_wordcloud.png"
    if create_wordcloud(word_counts, wordcloud_filename):
        # ワードクラウドを表示
        st.image(wordcloud_filename, caption="全体のワードクラウド", use_container_width=True)

    # 上位100単語を表形式で表示
    st.subheader("上位100単語")
    word_list = []
    for (word, part_of_speech), count in most_common_words:
        word_list.append([word, part_of_speech, count])
    df_words = pd.DataFrame(word_list, columns=["単語", "品詞", "出現回数"])

    # 単語がクリックされたときに文章を表示する機能
    all_sentences_option = "全ての文章を表示"
    # プルダウンリストの項目に集計数値を表示
    word_options = [f"{word} ({count})" for word, count in zip(df_words["単語"], df_words["出現回数"])]
    selected_word_with_count = st.selectbox("文章を表示する単語を選択してください", [all_sentences_option] + word_options)

    # 選択された単語の文字列から単語のみを抽出
    if selected_word_with_count != all_sentences_option:
        selected_word = selected_word_with_count.split('(')[0].strip()
    else:
        selected_word = all_sentences_option

    if selected_word:
        st.subheader(f"単語「{selected_word}」を含む文章")
        # 受付日時でソート
        sentence_data = sorted(sentence_data, key=lambda x: x.get("受付日時", ""), reverse=True)
        for sentence in sentence_data:
            if selected_word == all_sentences_option or selected_word in sentence["内容"]:
                st.write(f"**受付日時:** {sentence['受付日時']}")
                st.write(f"**内容:** {sentence['内容']}")
                st.write(f"**店舗:** {sentence['子要素']}")
                st.write("---")

    st.dataframe(df_words)

if __name__ == "__main__":
    main()
