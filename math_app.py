import streamlit as st
from openai import OpenAI
import os

# --- 0. 設定と準備 ---
# ※ APIキーは secrets.toml に保存されている前提です
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except:
    st.error("OpenAI APIキーが設定されていません。")
    st.stop()

st.set_page_config(page_title="Math Master AI", page_icon="🧮")

# --- 1. サイドバー（単元選択） ---
st.sidebar.title("🧮 数学マスター AI")
st.sidebar.caption("AIがあなたに合わせて無限に問題を作ります。")

grade = st.sidebar.selectbox("学年", ["中学1年生", "中学2年生", "中学3年生", "高校数学I・A"])

# 学年に応じて単元リストを変える
topics = []
if grade == "中学1年生":
    topics = ["正負の数", "文字式", "一次方程式", "比例・反比例", "平面図形(計算のみ)"]
elif grade == "中学2年生":
    topics = ["式の計算", "連立方程式", "一次関数", "図形の性質(角度)", "確率"]
elif grade == "中学3年生":
    topics = ["多項式・因数分解", "平方根", "二次方程式", "二次関数", "三平方の定理"]
else:
    topics = ["数と式", "集合と論証", "二次関数", "図形と計量(三角比)", "データの分析"]

selected_topic = st.sidebar.radio("単元を選択", topics)
difficulty = st.sidebar.select_slider("難易度", options=["基礎", "標準", "応用", "難問"], value="標準")

# --- 2. メイン処理 ---
st.title(f"{grade}: {selected_topic}")

# セッション状態の初期化
if "math_problem" not in st.session_state:
    st.session_state.math_problem = None
if "math_solution" not in st.session_state:
    st.session_state.math_solution = None

# 問題作成ボタン
if st.button("📝 問題を作成する", use_container_width=True):
    with st.spinner("AIが数式を計算中..."):
        # プロンプト：数式をLaTeX形式で書くように指示するのがコツ
        prompt = f"""
        あなたは数学のプロ講師です。以下の条件で数学の問題を1問作成してください。
        
        対象: {grade}
        単元: {selected_topic}
        難易度: {difficulty}
        
        【重要ルール】
        1. 数式は必ずLaTeX形式で書いてください。（例: $x^2 + 3x + 2 = 0$）
        2. 図形問題の場合は、文章だけで状況がわかる問題（角度計算など）にしてください。
        3. 出力は以下の形式のみにしてください。余計な挨拶は不要です。
        
        [問題]
        (ここに問題文)
        
        |||SPLIT|||
        
        [解答・解説]
        (ここに答えと、途中式を含めた丁寧な解説)
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini", # 数学は論理的なので4o-miniでもかなり優秀ですが、厳密な計算は4o推奨
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.choices[0].message.content
        
        if "|||SPLIT|||" in content:
            parts = content.split("|||SPLIT|||")
            st.session_state.math_problem = parts[0].strip()
            st.session_state.math_solution = parts[1].strip()
        else:
            st.session_state.math_problem = content
            st.session_state.math_solution = "解説の生成に失敗しました。"

# --- 3. 表示エリア ---
if st.session_state.math_problem:
    st.divider()
    st.subheader("Q. 問題")
    # StreamlitはMarkdownの中でLaTeX数式($...$)をきれいに表示してくれます
    st.markdown(st.session_state.math_problem)
    
    st.divider()
    
    # 解答を見るボタン（アコーディオン）
    with st.expander("👀 解答と解説を見る"):
        st.markdown(st.session_state.math_solution)
        
        st.info("💡 解説がわかりにくい場合は、下のチャットでAI先生に質問してみよう！")

# --- 4. 質問コーナー（簡易版） ---
if st.session_state.math_problem:
    user_question = st.text_input("解説について質問する", placeholder="例: なぜそこで移項するのですか？")
    if user_question:
        with st.spinner("解説中..."):
            qa_prompt = f"""
            先ほどの問題:
            {st.session_state.math_problem}
            
            解説:
            {st.session_state.math_solution}
            
            生徒からの質問:
            {user_question}
            
            これに対して、わかりやすく答えてください。数式はLaTeXを使用すること。
            """
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": qa_prompt}]
            )
            st.markdown(f"**AI先生:** {res.choices[0].message.content}")