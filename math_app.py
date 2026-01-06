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

# --- 0. 設定と準備 ---
# フォントの登録 (PDF生成用)
FONT_PATH = os.path.join(os.path.dirname(__file__), 'ipaexg.ttf')
try:
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont('IPAexG', FONT_PATH))
    else:
        # フォントがない場合は警告だけ出す（PDF生成時にエラーになるがアプリは落ちないように）
        pass
except Exception as e:
    print(f"Font Load Error: {e}")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except:
    st.error("OpenAI APIキーが設定されていません。")
    st.stop()

st.set_page_config(page_title="Math Master AI", page_icon="🧮", layout="wide")

# カスタムCSSでデザイン調整
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
    .problem-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #4CAF50;
        margin-bottom: 20px;
    }
    .dark-theme .problem-box {
        background-color: #262730;
        border-left: 5px solid #80bdff;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# PDF 生成関数
# ---------------------------------------------------------
def create_pdf(content_list, title, is_solution=False):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=20*mm, leftMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    
    styles = getSampleStyleSheet()
    # 日本語フォントスタイルを追加
    style_normal = ParagraphStyle(name='JapaneseNormal', parent=styles['Normal'], fontName='IPAexG', fontSize=10, leading=16)
    style_title = ParagraphStyle(name='JapaneseTitle', parent=styles['Heading1'], fontName='IPAexG', fontSize=16, leading=20, alignment=1)
    style_h2 = ParagraphStyle(name='JapaneseH2', parent=styles['Heading2'], fontName='IPAexG', fontSize=12, leading=16, spaceBefore=10)

    story = []
    story.append(Paragraph(title, style_title))
    story.append(Spacer(1, 10*mm))

    for i, item in enumerate(content_list, 1):
        if is_solution:
            text = item['solution']
        else:
            text = item['problem']
        
        # Markdownの改行をReportLab用に変換（簡易的）
        # 文中の数式はそのままテキストとして出力
        text = text.replace('\n', '<br/>')
        
        story.append(Paragraph(f"【第{i}問】", style_h2))
        story.append(Spacer(1, 2*mm))
        story.append(Paragraph(text, style_normal))
        story.append(Spacer(1, 8*mm))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ---------------------------------------------------------
# UI
# ---------------------------------------------------------

# --- サイドバー ---
with st.sidebar:
    st.title("🧮 Math Master AI")
    st.caption("AIがあなたに最適化された数学の問題を作成します。")
    st.divider()

    grade = st.selectbox("学年", ["中学1年生", "中学2年生", "中学3年生", "高校数学I・A", "高校数学II・B"])

    # 学年に応じた単元設定
    topics = []
    topic_details_map = {}

    if grade == "中学1年生":
        topic_details_map = {
            "正負の数": "正負の数 (Numbers): プラスとマイナス（正の数・負の数）、加法・減法（足し算・引き算）、乗法・除法（掛け算・割り算）、四則混合計算",
            "文字と式": "文字と式 (Algebraic Expressions): 文字を使った式（$x$ や $a$ の導入）、式の計算（$3x + 2x$ など）、関係を表す式（等式・不等式）",
            "一次方程式": "一次方程式 (Linear Equations): 方程式の解き方（移項など）、方程式の利用（文章題 ※難所なので丁寧に）",
            "比例・反比例": "比例・反比例 (Proportions): 関数、比例の式とグラフ ($y = ax$)、反比例の式とグラフ ($y = a/x$)",
            "平面図形": "平面図形 (Plane Figures): 直線と角、図形の移動（平行移動・回転移動・対称移動）、基本の作図（垂直二等分線・角の二等分線）、円とおうぎ形（長さ・面積）",
            "空間図形": "空間図形 (Spatial Figures): 立体のいろいろ（角柱・円柱・角錐・円錐・多面体）、立体の見方（投影図・展開図）、表面積と体積",
            "データの活用": "データの活用 (Data Handling): 度数分布表・ヒストグラム、代表値（平均値・中央値・最頻値）、相対度数"
        }
        topics = list(topic_details_map.keys())
    elif grade == "中学2年生":
        topics = ["式の計算", "連立方程式", "一次関数", "図形の性質", "確率"]
    elif grade == "中学3年生":
        topics = ["多項式・因数分解", "平方根", "二次方程式", "二次関数", "三平方の定理"]
    elif grade == "高校数学I・A":
        topics = ["数と式", "集合と論証", "二次関数", "図形と計量", "データの分析", "場合の数と確率"]
    else:
        topics = ["式と証明", "複素数と方程式", "図形と方程式", "三角関数", "指数・対数関数", "微分・積分"]

    selected_topic = st.radio("単元を選択", topics)
    topic_detail = topic_details_map.get(selected_topic, "")
    
    st.divider()
    
    col_diff, col_num = st.columns(2)
    with col_diff:
        difficulty = st.select_slider("難易度", options=["基礎", "標準", "応用", "難問"], value="標準")
    with col_num:
        num_questions = st.number_input("問題数", min_value=1, max_value=10, value=3)

    generate_btn = st.button("🚀 問題を作成する", key="gen_btn")

# --- メインエリア ---
st.title(f"{grade}: {selected_topic}")

# セッション状態の管理
if "problems_list" not in st.session_state:
    st.session_state.problems_list = []

# 生成処理
if generate_btn:
    st.session_state.problems_list = [] # リセット
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(num_questions):
        status_text.text(f"問題 {i+1} / {num_questions} を生成中...")
        
        prompt = f"""
        あなたは数学のプロ講師です。以下の条件で数学の問題を1問作成してください。
        
        対象: {grade}
        単元: {selected_topic}
        {f"学習範囲詳細: {topic_detail}" if topic_detail else ""}
        難易度: {difficulty}
        
        【重要ルール】
        1. 数式はLaTeX形式で記述してください（例: $x^2 + 3x + 2 = 0$）。
        2. 図形問題は文章だけで状況が伝わるように工夫してください。
        3. 出力は以下のセパレーターで区切ってください。
        
        [問題]
        (ここに問題文)
        
        |||SPLIT|||
        
        [解答・解説]
        (ここに答えと、途中式を含めた解説)
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
                sol = "解説の生成に失敗しました。"
            
            st.session_state.problems_list.append({
                "id": i+1,
                "problem": prob,
                "solution": sol
            })
            
        except Exception as e:
            st.error(f"生成中にエラーが発生しました: {e}")
        
        progress_bar.progress((i + 1) / num_questions)
        
    status_text.success("生成完了！")
    progress_bar.empty()

# 表示処理
if st.session_state.problems_list:
    
    # --- PDF ダウンロード ---
    st.subheader("📥 ダウンロード")
    col_pdf1, col_pdf2 = st.columns(2)
    
    # 問題PDF
    pdf_prob = create_pdf(st.session_state.problems_list, f"{grade} {selected_topic} - 問題編", is_solution=False)
    col_pdf1.download_button(
        label="📄 問題PDFを保存",
        data=pdf_prob,
        file_name="math_problems.pdf",
        mime="application/pdf",
        use_container_width=True
    )
    
    # 解答PDF
    pdf_sol = create_pdf(st.session_state.problems_list, f"{grade} {selected_topic} - 解答・解説編", is_solution=True)
    col_pdf2.download_button(
        label="📝 解答PDFを保存",
        data=pdf_sol,
        file_name="math_solutions.pdf",
        mime="application/pdf",
        use_container_width=True
    )
    
    st.divider()
    
    # --- 個別の問題表示 ---
    for item in st.session_state.problems_list:
        with st.container():
            st.markdown(f"### Q{item['id']}.")
            # 問題文
            st.markdown(item['problem'])
            
            # アコーディオンで解答
            with st.expander(f"Q{item['id']} の解答・解説を見る"):
                st.markdown(item['solution'])
                
            st.divider()

    # --- 質問コーナー（全体用、もしくは最後にまとめて） ---
    # 簡易的に最後の問題について聞けるようにするか、全体フォームにするか
    # ここでは「任意の質問」として設置
    st.subheader("👩‍🏫 AI先生に質問")
    user_question = st.text_input("わからないことがあれば聞いてください", placeholder="例: Q2の解説について、もっと詳しく教えて")
    if user_question:
        with st.spinner("AI先生が回答中..."):
            # 文脈として全問題を渡すのは重いので、ユーザーの質問に関連しそうな情報を渡すか、
            # シンプルに「直前の会話」として渡す設計にするのが通常だが、ここは簡易実装
            context = ""
            for p in st.session_state.problems_list:
                context += f"Q{p['id']}: {p['problem']}\nAnswer: {p['solution']}\n\n"
            
            qa_prompt = f"""
            以下の数学の問題セットに関する生徒からの質問に答えてください。
            
            【問題データ】
            {context}
            
            【生徒の質問】
            {user_question}
            
            親切に、わかりやすく、LaTeX数式を使って解説してください。
            """
            
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": qa_prompt}]
            )
            st.markdown(f"**AI先生:** {res.choices[0].message.content}")