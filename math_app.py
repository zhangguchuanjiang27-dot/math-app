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
        # 余白
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

    # 学年に応じた単元設定
    topic_details_map = {}
    if grade == "中学1年生":
        topic_details_map = {
            "正負の数": "正負の数 (Numbers): プラスとマイナス、四則混合計算",
            "文字と式": "文字と式 (Algebraic Expressions): 文字式の計算、等式・不等式",
            "一次方程式": "一次方程式 (Linear Equations): 計算と文章題",
            "比例・反比例": "比例・反比例 (Proportions): 式とグラフ",
            "平面図形": "平面図形 (Plane Figures): 作図、円とおうぎ形",
            "空間図形": "空間図形 (Spatial Figures): 表面積と体積",
            "データの活用": "データの活用: 平均値、度数分布表"
        }
    elif grade == "中学2年生":
        topic_details_map = {"式の計算": "", "連立方程式": "", "一次関数": "", "図形の性質": "", "確率": ""}
    elif grade == "中学3年生":
        topic_details_map = {"多項式・因数分解": "", "平方根": "", "二次方程式": "", "二次関数": "", "三平方の定理": ""}
    elif grade == "高校数学I・A":
        topic_details_map = {"数と式": "", "二次関数": "", "図形と計量": "", "データの分析": "", "場合の数と確率": ""}
    else:
        topic_details_map = {"式と証明": "", "複素数と方程式": "", "図形と方程式": "", "三角関数": "", "指数・対数関数": "", "微分・積分": ""}

    topics = list(topic_details_map.keys())
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
        数学の問題を作成。対象:{grade}, 単元:{selected_topic}, 難易度:{difficulty}
        重要: 数式はLaTeX形式($...$)で記述。図形問題は文章のみで成立させること。
        
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
    st.subheader("📥 ダウンロード")
    col_pdf1, col_pdf2 = st.columns(2)
    
    # PDF生成実行
    pdf_prob = create_pdf(st.session_state.problems_list, f"{grade} {selected_topic} - 問題編", is_solution=False)
    pdf_sol = create_pdf(st.session_state.problems_list, f"{grade} {selected_topic} - 解答編", is_solution=True)
    
    if pdf_prob:
        col_pdf1.download_button("📄 問題PDF", pdf_prob, "math_problems.pdf", "application/pdf", use_container_width=True)
    if pdf_sol:
        col_pdf2.download_button("📝 解答PDF", pdf_sol, "math_solutions.pdf", "application/pdf", use_container_width=True)
    
    st.divider()
    
    for item in st.session_state.problems_list:
        st.markdown(f"### Q{item['id']}.")
        st.markdown(item['problem'])
        with st.expander("解答を見る"):
            st.markdown(item['solution'])
        st.divider()