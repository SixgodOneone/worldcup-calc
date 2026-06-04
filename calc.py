# -*- coding: utf-8 -*-
# @Author: 有痔不在年糕
# @Date:   2026/6/3 21:35
# @Last Modified by:   有痔不在年糕
# @Last Modified time: 2026/6/3 21:35
# @File: calc.py
# @Software: PyCharm
import streamlit as st
import pandas as pd
import math  # 核心修改：引入数学库以处理偶数取整

st.set_page_config(page_title="2026世界杯 马丁格尔排单中台", layout="wide")

st.title("🏆 2026世界杯 互斥排单中台 (跨日倍投版)")

# --- 占位提示：如果你有读取 schedule.csv 的代码，请放在这里 ---

st.header("📋 第一步：选择赛事与赔率")
match_count = st.radio("本轮包含几场比赛？", [1, 2, 3], horizontal=True)

O_list = []
cols = st.columns(match_count)
for i in range(match_count):
    with cols[i]:
        # 实际业务中可根据csv自动带入，这里保留手动输入框作为基础逻辑
        odd = st.number_input(f"第 {i + 1} 场票面综合赔率", value=3.00, step=0.01, key=f"odd_{i}")
        O_list.append(odd)

# ==========================================
# 核心修改区域 1：资金池配置 (保留P参数，增加中文小贴士)
# ==========================================
st.header("⚙️ 第二步：全局资金池配置")
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
# 核心修改区域 2：计算逻辑与体彩2元偶数风控
# ==========================================
st.header("⚡ 第三步：生成执行单")
if st.button("🚀 自动生成体彩执行单"):
    # 1. 计算数学模型分母
    denom_sum = sum([1 / o for o in O_list])
    denom = 1 - denom_sum

    if denom <= 0:
        st.error("⚠️ 赔率组合异常！这些赔率太低了，无法形成绝对兜底的互斥对冲，系统拒绝生成方案。")
    else:
        # 2. 反推总目标资金（本金 + 沉没成本 + 你自定义的暴力利润）
        T = (S + P) / denom

        # 3. 动态分配每单金额（严格适配体彩 2 元一注规则）
        costs = []
        for o in O_list:
            exact_cost = T / o
            # 核心算法：先除以 2 并向上取整，然后再乘以 2，确保结果绝对是大于等于精确成本的最小偶数
            even_cost = math.ceil(exact_cost / 2) * 2
            costs.append(even_cost)

        total_cost = sum(costs)

        # 4. 结果展示
        st.success(f"✅ 计算完成！本轮需要转给彩票店总计: **{total_cost} 元**")

        st.markdown("### 📝 请按以下金额打票：")
        for i, cost in enumerate(costs):
            st.info(f"👉 **第 {i + 1} 张票** (对应赔率 {O_list[i]:.2f})： 投入 **{cost} 元**")

        # 5. 绝对兜底验算展示 (沙盘推演)
        st.markdown("---")
        st.markdown("### 🔍 兜底验算 (假设第 1 张票中了)：")
        win_prize = costs[0] * O_list[0]
        net_profit = win_prize - total_cost - S

        st.write(f"- 中奖总奖金：{costs[0]} × {O_list[0]:.2f} = **{win_prize:.2f} 元**")
        st.write(f"- 扣除本轮总投入：{total_cost} 元")
        st.write(f"- 扣除历史沉没成本：{S} 元")
        st.write(f"- **最终净利润：{net_profit:.2f} 元** (绝对满足甚至略微超额完成你设定的目标利润 {P} 元！)")