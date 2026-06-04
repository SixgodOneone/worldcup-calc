# -*- coding: utf-8 -*-
# @Author: 有痔不在年糕
# @Date:   2026/6/3 21:35
# @Last Modified by:   有痔不在年糕
# @Last Modified time: 2026/6/3 21:35
# @File: calc.py
# @Software: PyCharm
import streamlit as st
import pandas as pd

st.set_page_config(page_title="2026世界杯排单中台", layout="centered")

st.title("⚽ 世界杯马丁格尔排单中台")
st.markdown("---")


# 1. 后台静默调用赛程数据库
@st.cache_data
def load_data():
    return pd.read_csv("schedule.csv")


try:
    df = load_data()
except FileNotFoundError:
    st.error("⚠️ 找不到 schedule.csv 文件，请确认它就在 calc.py 的旁边！")
    st.stop()

# 2. 界面第一步：可视化赛程查阅
st.header("📅 第一步：赛事池检索")
# 提取所有比赛日
all_dates = sorted(df['日期'].unique().tolist())
selected_date = st.selectbox("请选择今日执行排单的日期：", all_dates)

# 过滤并展示当天的比赛
today_matches = df[df['日期'] == selected_date].copy()
st.write(f"**{selected_date} 可选赛事（共 {len(today_matches)} 场）：**")
st.dataframe(today_matches, use_container_width=True, hide_index=True)

st.markdown("---")

# 3. 界面第二步：跨日资金结转
st.header("⚙️ 第二步：全局资金池配置")
col1, col2, col3 = st.columns(3)
with col1:
    n = st.number_input("初始单注基准 (n)", value=100)
with col2:
    S = st.number_input("累计沉没成本 (S)", value=0, help="如果前一天全黑，填入总亏损额")
with col3:
    P = st.number_input("本轮目标利润", value=n)

double_odds = st.number_input("胜/负双选综合折算赔率 (默认即可)", value=1.25, step=0.01)

st.markdown("---")

# 4. 界面第三步：动态生成排单算法
st.header("📝 第三步：互斥打包执行")
match_count = st.radio("本轮排单包包含几场比赛？", [1, 2, 3, 4], horizontal=True)

st.write(f"请输入这 **{match_count}** 场比赛的【平局赔率】：")

# 动态生成赔率输入框
odds_inputs = []
cols = st.columns(match_count)
for i in range(match_count):
    with cols[i]:
        odd = st.number_input(f"第 {i + 1} 场", value=3.00, step=0.01, key=f"odd_{i}")
        odds_inputs.append(odd)

st.markdown("---")

# 5. 生成输出流
if st.button("⚡ 自动生成执行单", type="primary"):
    # 动态计算所有场次的综合赔率
    O_list = []
    for i in range(match_count):
        # 赔率折算：双选赔率的i次方 * 对应场次的平赔
        current_O = (double_odds ** i) * odds_inputs[i]
        O_list.append(current_O)

    # 计算数学模型分母
    sum_inverse_O = sum([1 / o for o in O_list])
    denom = 1 - sum_inverse_O

    if denom <= 0:
        st.error(
            "⚠️ 致命风控拦截：您选的这几场赔率组合过低，数学底层已被击穿（无论怎么买都会亏损）。请放弃本轮打包或减少场次！")
    else:
        # 反推总目标资金
        T = (S + P) / denom

        # 动态分配每单金额
        costs = []
        for o in O_list:
            costs.append(int((T / o) + 1))

        total_cost = sum(costs)

        st.success("✅ 模型推算成功！SOP 指令已生成：")

        # 动态拼接发送给网点的话术
        msg = f"老板，打以下互斥单，出票后拍照：\n\n"
        for i in range(match_count):
            if i == 0:
                msg += f"**单子 {i + 1}：** 第 1 场【平】 —— 打 **{costs[i]}** 元\n"
            else:
                prefix = " 串 ".join([f"第 {j + 1} 场【胜/负】" for j in range(i)])
                msg += f"**单子 {i + 1}：** {prefix} 串 第 {i + 1} 场【平】 —— 打 **{costs[i]}** 元\n"

        msg += f"\n*本次操作总计转账额：**{total_cost}** 元*"

        st.info(msg)
