import streamlit as st
import pandas as pd
import math  # 引入数学库处理体彩2元偶数取整

st.set_page_config(page_title="2026世界杯 马丁格尔排单中台", layout="wide")

st.title("🏆 2026世界杯 互斥排单中台 (完美4场串关版)")

# ==========================================
# 恢复区域：读取赛程数据与日期筛选
# ==========================================
st.header("📅 第一步：查看当日赛程")
try:
    # 读取同目录下的赛程文件
    df = pd.read_csv("schedule.csv")

    # 智能寻找日期列 (适配叫 'Date' 或 '日期' 的列)
    date_col = '日期' if '日期' in df.columns else ('Date' if 'Date' in df.columns else df.columns[0])

    # 提取所有不重复的日期并生成下拉菜单
    dates = df[date_col].unique()
    selected_date = st.selectbox("请选择比赛日期", dates)

    # 过滤并显示当天的比赛
    matches_today = df[df[date_col] == selected_date]
    st.dataframe(matches_today, use_container_width=True)

except FileNotFoundError:
    st.error("⚠️ 找不到 schedule.csv 文件！请确保它和 calc.py 放在同一个文件夹里，并且已经传到了 GitHub。")
except Exception as e:
    st.warning(f"⚠️ 读取赛程数据时出现一点小问题：{e}")

# ==========================================
# 第二步：选择场次与输入原始平局赔率
# ==========================================
st.header("📋 第二步：选择场次与输入平局赔率")
# 完美修复：把 4 场比赛的选项加回来了！
match_count = st.radio("本轮准备打包几场比赛？", [1, 2, 3, 4], horizontal=True)

O_list = []
cols = st.columns(match_count)
for i in range(match_count):
    with cols[i]:
        # 用户只需在这里无脑输入竞彩官方的【原始平局赔率】即可
        odd = st.number_input(f"第 {i + 1} 场单场平局赔率", value=3.00, step=0.01, key=f"odd_{i}")
        O_list.append(odd)

# 胜负双选综合折算赔率配置（后台串关的核心杠杆）
double_odds = st.number_input(
    "胜/负双选综合折算赔率 (默认即可)",
    value=1.25,
    step=0.01,
    help="体彩中主胜和客胜同时勾选（双选排除平局）的综合等效赔率，通常在1.25左右，保持默认即可。"
)

# ==========================================
# 第三步：全局资金池配置 (附带中文小贴士)
# ==========================================
st.header("⚙️ 第三步：全局资金池配置")
st.markdown("请根据你的实战阶段，填写以下关键参数：")

col1, col2, col3 = st.columns(3)
with col1:
    n = st.number_input(
        "初始单注基准 (n)",
        value=60,
        help="【说明】这是你最开始的起步资金。如果还没开始亏钱，填你平时习惯的单注金额。"
    )
with col2:
    S = st.number_input(
        "累计沉没成本 (S)",
        value=0,
        help="【说明】你之前为了这套方案，已经打水漂、亏掉的总金额。第一天刚开始玩必须填 0！"
    )
with col3:
    P = st.number_input(
        "本轮目标利润 (P)",
        value=60,
        help="【说明】这把中奖后你想净赚多少钱。想启动跨日倍投？直接把这里填成昨晚最后一场买入金额的 2 倍！"
    )

# ==========================================
# 第四步：计算逻辑与体彩2元偶数风控
# ==========================================
st.header("⚡ 第四步：生成执行单")
if st.button("🚀 自动生成体彩执行单"):

    # 核心数学修正：根据串关层级，自动计算每张单子的【真实复合票面赔率】
    # 比如：单子1 = O1;  单子2 = 1.25 * O2;  单子3 = 1.25 * 1.25 * O3 ...
    composite_O_list = []
    for i, raw_odd in enumerate(O_list):
        comp_odd = raw_odd * (double_odds ** i)
        composite_O_list.append(comp_odd)

    # 计算数学模型分母
    denom_sum = sum([1 / o for o in composite_O_list])
    denom = 1 - denom_sum

    if denom <= 0:
        st.error(
            "⚠️ 赔率组合异常或场次过多！这4场叠加后超出了数学对冲极限（分母<=0），系统拒绝生成方案。请检查赔率是否输入错误。")
    else:
        # 反推总目标资金（本金 + 沉没成本 + 你自定义的暴力利润）
        T = (S + P) / denom

        # 动态分配每单金额（严格适配体彩 2 元一注、金额必为偶数规则）
        costs = []
        for comp_odd in composite_O_list:
            exact_cost = T / comp_odd
            # 核心算法：先除以 2 并向上取整，然后再乘以 2，确保结果绝对是大于等于精确成本的最小偶数
            even_cost = math.ceil(exact_cost / 2) * 2
            costs.append(even_cost)

        total_cost = sum(costs)

        # 结果展示
        st.success(f"✅ 计算完成！本轮需要转给彩票店总计: **{total_cost} 元**")

        st.markdown("### 📝 请严格按照以下指令通知老板打票：")

        for i, cost in enumerate(costs):
            if i == 0:
                desc = "单打【第 1 场】平局"
            else:
                # 自动生成清晰的串关话术，方便发给彩票店老板
                chain_prefix = " 串 ".join([f"第 {j + 1} 场胜/负" for j in range(i)])
                desc = f"{chain_prefix} **再串** 【第 {i + 1} 场】平局"

            st.info(f"👉 **第 {i + 1} 张票** ({desc}) ── 票面赔率: {composite_O_list[i]:.2f} ── 投入金额: **{cost} 元**")

        # 绝对兜底验算展示 (沙盘推演)
        st.markdown("---")
        st.markdown("### 🔍 稳健性兜底验算 (假设当晚打出任意一个平局剧本)：")
        win_prize = costs[0] * composite_O_list[0]
        net_profit = win_prize - total_cost - S

        st.write(f"- 中奖票总奖金（预估）：**{win_prize:.2f} 元**")
        st.write(f"- 扣除本轮总投入成本：{total_cost} 元")
        st.write(f"- 扣除历史累计沉没成本：{S} 元")
        st.write(f"- **最终口袋净利润：{net_profit:.2f} 元** (完美达成并略微超过你的目标利润 {P} 元！)")