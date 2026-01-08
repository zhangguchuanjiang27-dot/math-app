import streamlit as st
from openai import OpenAI
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.fonts import addMapping

# --- 0. 設定と準備 ---

# 日本語フォントの設定
FONT_FILE = 'ipaexg.ttf'
FONT_PATH = os.path.join(os.path.dirname(__file__), FONT_FILE)

# デフォルトは英語フォント（ファイルがない場合用）
japanese_font_name = "Helvetica" 

try:
    if os.path.exists(FONT_PATH):
        # フォント登録
        pdfmetrics.registerFont(TTFont('IPAexG', FONT_PATH))
        
        # 太字や斜体のマッピング（同じフォントファイルを使って擬似的に対応させる設定）
        addMapping('IPAexG', 0, 0, 'IPAexG') # Normal
        addMapping('IPAexG', 0, 1, 'IPAexG') # Italic
        addMapping('IPAexG', 1, 0, 'IPAexG') # Bold
        addMapping('IPAexG', 1, 1, 'IPAexG') # Bold Italic
        
        japanese_font_name = "IPAexG"
    else:
        st.warning(f"⚠️ フォントファイル '{FONT_FILE}' が見つかりません。PDFの日本語部分は文字化け、または表示されません。")
except Exception as e:
    st.error(f"フォント設定エラー: {e}")

# OpenAI設定
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except:
    st.error("OpenAI APIキーが設定されていません。")
    st.stop()

st.set_page_config(page_title="Math Master AI", page_icon="🧮", layout="wide")

# CSS
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        border-radius: 10px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #45a049;
        transform: scale(1.02);
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# PDF 生成関数（修正版）
# ---------------------------------------------------------
def create_pdf(content_list, title, is_solution=False):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=20*mm, leftMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    
    styles = getSampleStyleSheet()
    
    # ★修正ポイント: Heading1を使わず、Normalをベースに自作する
    # これにより「勝手に太字にしようとしてエラーになる」のを防ぎます
    style_normal = ParagraphStyle(
        name='JapaneseNormal', 
        parent=styles['Normal'], 
        fontName=japanese_font_name, 
        fontSize=10, 
        leading=16
    )
    
    style_title = ParagraphStyle(
        name='JapaneseTitle', 
        parent=styles['Normal'], # Heading1ではなくNormalを継承
        fontName=japanese_font_name, 
        fontSize=18, 
        leading=22, 
        alignment=1, # 中央揃え
        spaceAfter=10*mm
    )
    
    style_h2 = ParagraphStyle(
        name='JapaneseH2', 
        parent=styles['Normal'], # Heading2ではなくNormalを継承
        fontName=japanese_font_name, 
        fontSize=12, 
        leading=16, 
        spaceBefore=5*mm,
        spaceAfter=2*mm,
        textColor="black"
    )

    story = []
    
    # タイトル追加
    story.append(Paragraph(title, style_title))

    for i, item in enumerate(content_list, 1):
        if is_solution:
            text = item['solution']
        else:
            text = item['problem']
        
        # 改行コードを <br/> に変換
        text = text.replace('\n', '<br/>')
        
        # 問題番号
        story.append(Paragraph(f"【第{i}問】", style_h2))
        # 本文
        story.append(Paragraph(text, style_normal))
        
        # 余白設定 (問題編の場合は、生徒が計算を書くためのスペースを空ける)
        if not is_solution:
            story.append(Spacer(1, 50*mm)) # 5cm分の計算スペース
        else:
            story.append(Spacer(1, 5*mm))
    
    # ビルド（エラー時はキャッチしてNoneを返す安全策）
    try:
        doc.build(story)
    except Exception as e:
        st.error(f"PDF生成中にエラーが発生しました: {e}")
        return None

    buffer.seek(0)
    return buffer

# ---------------------------------------------------------
# UI & ロジック
# ---------------------------------------------------------

# --- サイドバー ---
with st.sidebar:
    st.title("🧮 Math Master AI")
    st.caption("AIがあなたに最適化された数学の問題を作成します。")
    st.divider()

    grade = st.selectbox("学年", ["中学1年生", "中学2年生", "中学3年生", "高校数学I・A", "高校数学II・B"])

    # 学年ごとの単元とサブカテゴリの定義
    category_map = {}
    
    if grade == "中学1年生":
        category_map = {
            "正負の数 (Numbers)": [
                "指定なし (ランダム)",
                "プラスとマイナス（正の数・負の数）",
                "加法・減法（足し算・引き算）",
                "乗法・除法（掛け算・割り算）",
                "四則混合計算"
            ],
            "文字と式 (Algebraic Expressions)": [
                "指定なし (ランダム)",
                "文字を使った式（x や a の導入）",
                "式の計算（3x + 2x など）",
                "関係を表す式（等式・不等式）"
            ],
            "一次方程式 (Linear Equations)": [
                "指定なし (ランダム)",
                "方程式の解き方（移項など）",
                "方程式の利用（文章題）"
            ],
            "比例・反比例 (Proportions)": [
                "指定なし (ランダム)",
                "関数とは",
                "比例の式とグラフ (y = ax)",
                "反比例の式とグラフ (y = a/x)"
            ],
            "平面図形 (Plane Figures)": [
                "指定なし (ランダム)",
                "直線と角",
                "図形の移動（平行移動・回転移動・対称移動）",
                "基本の作図（垂直二等分線・角の二等分線）",
                "円とおうぎ形（長さ・面積）"
            ],
            "空間図形 (Spatial Figures)": [
                "指定なし (ランダム)",
                "立体のいろいろ（角柱・円柱・角錐・円錐・多面体）",
                "立体の見方（投影図・展開図）",
                "表面積と体積"
            ],
            "データの活用": []
        }
    elif grade == "中学2年生":
        category_map = {k: [] for k in ["式の計算", "連立方程式", "一次関数", "図形の性質", "確率"]}
    elif grade == "中学3年生":
        category_map = {k: [] for k in ["多項式・因数分解", "平方根", "二次方程式", "二次関数", "三平方の定理"]}
    elif grade == "高校数学I・A":
        category_map = {k: [] for k in ["数と式", "二次関数", "図形と計量", "データの分析", "場合の数と確率"]}
    else:
        category_map = {k: [] for k in ["式と証明", "複素数と方程式", "図形と方程式", "三角関数", "指数・対数関数", "微分・積分"]}

    # 単元選択UI
    main_topic = st.selectbox("単元を選択", list(category_map.keys()))
    
    # サブカテゴリ選択UI
    sub_topics = category_map.get(main_topic, [])
    selected_subtopic = ""
    if sub_topics:
        selected_subtopic = st.selectbox("詳細ジャンル", sub_topics)
    
    # プロンプト用の最終的な単元文字列を作成
    final_topic = main_topic
    if selected_subtopic and selected_subtopic != "指定なし (ランダム)":
        final_topic += f" - {selected_subtopic}"
    
    st.divider()
    col_diff, col_num = st.columns(2)
    with col_diff:
        difficulty = st.select_slider("難易度", options=["基礎", "標準", "応用", "難問"], value="標準")
    with col_num:
        num_questions = st.number_input("問題数", min_value=1, max_value=10, value=3)

    generate_btn = st.button("🚀 問題を作成する", key="gen_btn")

# --- メインエリア ---
st.title(f"{grade}: {final_topic}")

if "problems_list" not in st.session_state:
    st.session_state.problems_list = []

# 生成処理
if generate_btn:
    st.session_state.problems_list = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(num_questions):
        status_text.text(f"問題 {i+1} / {num_questions} を生成中...")
        
        prompt = f"""
        数学の問題を作成。
        対象学年: {grade}
        指定単元: {final_topic}
        難易度: {difficulty}
        
        【重要なお願い】
        ・必ず「{final_topic}」に関連する問題を作成してください。他の単元の問題は混ぜないでください。
        ・例えば「文章題」が選択されている場合は、単なる計算問題ではなく文章題を作成してください。
        ・「計算」が選択されている場合は、計算問題を作成してください。
        
        【学習指導要領への適合（超重要）】
        選択された学年（{grade}）で学習する範囲内の知識だけで解ける問題にしてください。
        特に以下の点に注意してください：
        - {grade}が「中学1年生」の場合：
           ★「三平方の定理（ピタゴラスの定理）」は絶対に使用禁止。
           ★「相似」「円周角の定理」「平方根（ルート）」も使用禁止。
           ★円周率は「π」を使用すること（3.14ではなく）。
        - {grade}が「中学2年生」の場合：
           ★「三平方の定理」「相似」「二次方程式」は使用禁止。
        
        重要: 数式はPDF出力時に文字化けを防ぐため、LaTeX形式($...$)は使用せず、一般的なテキスト表記（例: x, 2x, 1/3, x^2）で記述すること。図形問題は文章のみで成立させること。
        
        出力フォーマット:
        [問題]
        (問題文)
        |||SPLIT|||
        [解答・解説]
        (解説文)
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content
            
            if "|||SPLIT|||" in content:
                parts = content.split("|||SPLIT|||")
                prob = parts[0].replace("[問題]", "").strip()
                sol = parts[1].replace("[解答・解説]", "").strip()
            else:
                prob = content
                sol = "解説生成エラー"
            
            st.session_state.problems_list.append({"id": i+1, "problem": prob, "solution": sol})
            
        except Exception as e:
            st.error(f"Error: {e}")
        
        progress_bar.progress((i + 1) / num_questions)
        
    status_text.success("完了！")
    progress_bar.empty()

# 表示処理
if st.session_state.problems_list:
    # PDFボタンは編集後に表示するため、ここでの表示は削除し、ループ後に移動します。
    st.info("以下のテキストエリアで問題文や解説を編集できます。編集内容はPDFに反映されます。")
    st.divider()
    
    for i, item in enumerate(st.session_state.problems_list):
        st.subheader(f"Q{item['id']}.")
        
        # 問題文の編集
        new_prob = st.text_area(f"問題文 (Q{item['id']})", value=item['problem'], key=f"prob_{item['id']}", height=150)
        item['problem'] = new_prob  # 状態の更新
        
        # 画像があれば表示
        if item.get('image_data'):
             pass # Removed image support
            
        # 解答・解説の編集
        with st.expander("解答・解説を編集"):
            new_sol = st.text_area(f"解説文 (Q{item['id']})", value=item['solution'], key=f"sol_{item['id']}", height=150)
            item['solution'] = new_sol # 状態の更新
            
        # プレビュー（数式確認用）
        with st.expander("プレビューを確認 (数式等の表示チェック)"):
            st.markdown("**[問題]**")
            st.markdown(item['problem'])
            st.markdown("**[解説]**")
            st.markdown(item['solution'])
            
        st.divider()

    # --- PDF生成 & ダウンロード (編集後の内容で作成) ---
    st.subheader("📥 ダウンロード")
    col_pdf1, col_pdf2 = st.columns(2)
    
    # PDF生成実行
    pdf_prob = create_pdf(st.session_state.problems_list, f"{grade} {final_topic} - 問題編", is_solution=False)
    pdf_sol = create_pdf(st.session_state.problems_list, f"{grade} {final_topic} - 解答編", is_solution=True)
    
    if pdf_prob:
        col_pdf1.download_button("📄 問題PDF", pdf_prob, "math_problems.pdf", "application/pdf", use_container_width=True)
    if pdf_sol:
        col_pdf2.download_button("📝 解答PDF", pdf_sol, "math_solutions.pdf", "application/pdf", use_container_width=True)