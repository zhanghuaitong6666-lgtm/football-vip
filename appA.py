import streamlit as st
import pandas as pd
import numpy as np
import pickle
import os

st.set_page_config(page_title="足球赛事盘口监控", layout="wide")

# ==========================================
# 🔐 第一道防线：带权限隔离的 VIP 登录墙
# ==========================================

# 【桐哥必看】：这里配置账号、密码和权限！
# role: "admin" 代表超级管理员（你），能改数据、能保存。
# role: "viewer" 代表VIP客户（买家），只能看，不能改任何东西！
VALID_USERS = {
    "tongge": {"password": "888", "role": "admin"},       # 你的大号 (密码我改简单了，你自己可以随便换)
    "vip01":  {"password": "123", "role": "viewer"},      # 卖给张三的号 (纯看客)
    "vip02":  {"password": "666", "role": "viewer"}       # 卖给李四的号 (纯看客)
}

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = ""
    st.session_state.role = ""

def login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>🔐 专业赛事盘口精算系统</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>商业版 | 数据实时同步 | 严禁外传</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            st.markdown("### 欢迎登录")
            username = st.text_input("👤 专属账号")
            password = st.text_input("🔑 登录密码", type="password")
            
            if st.button("🚀 立即进入大盘", use_container_width=True, type="primary"):
                if username in VALID_USERS and VALID_USERS[username]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    st.session_state.role = VALID_USERS[username]["role"]
                    st.success("✅ 验证成功！正在加载底层数据...")
                    st.rerun()
                else:
                    st.error("❌ 账号或密码错误，或订阅已过期！")

def logout():
    st.session_state.logged_in = False
    st.session_state.current_user = ""
    st.session_state.role = ""
    st.rerun()

# 如果没登录，卡死在这里
if not st.session_state.logged_in:
    login_page()
    st.stop()


# ==========================================
# ⚽ 第二阶段：核心业务系统 (根据身份展示不同界面)
# ==========================================

# 读写你的 v3 存档，确保你的数据一点不丢！
MATCHES_FILE = "matches_data_v3.pkl"
ODDS_FILE = "odds_data_v3.pkl"

with st.sidebar:
    if st.session_state.role == "admin":
        st.success(f"👑 超级管理员：**{st.session_state.current_user}**")
    else:
        st.info(f"👁️ VIP观盘用户：**{st.session_state.current_user}**")
        
    if st.button("🚪 安全退出登录", use_container_width=True):
        logout()
        
    st.divider()
    
    # ⚡⚡⚡ 核心权限控制：只有 admin 才能看到下面这些按钮！⚡⚡⚡
    if st.session_state.role == "admin":
        st.header("💾 后台数据管理台 (客户不可见)")
        st.markdown("更新完盘口后，务必点击下方保存。")
        
        if st.button("📥 永久保存同步大盘数据", use_container_width=True, type="primary"):
            with open(MATCHES_FILE, 'wb') as f:
                pickle.dump(st.session_state.matches_df, f)
            with open(ODDS_FILE, 'wb') as f:
                pickle.dump(st.session_state.odds_data, f)
            st.success("✅ 数据已同步！客户刷新即可看到最新胜率。")

        if st.button("🗑️ 清空当前大盘", use_container_width=True):
            if os.path.exists(MATCHES_FILE): os.remove(MATCHES_FILE)
            if os.path.exists(ODDS_FILE): os.remove(ODDS_FILE)
            for key in list(st.session_state.keys()):
                if key not in ['logged_in', 'current_user', 'role']:
                    del st.session_state[key]
            st.rerun()

        st.divider()
        st.markdown("**极速导入区**")
        uploaded_file = st.file_uploader("上传 CSV 赛程文件", type=["csv"])
        if uploaded_file is not None:
            try:
                new_df = pd.read_csv(uploaded_file)
                st.session_state.matches_df = pd.concat([st.session_state.matches_df, new_df], ignore_index=True)
                st.success("导入成功！请点击上方保存。")
            except Exception as e:
                st.error(f"导入失败: {e}")
    else:
        st.markdown("🔒 **观盘模式声明**")
        st.markdown("当前账号仅具备**实时数据查看权限**。大盘数据由后台专业精算师团队实时更新，请在页面右侧筛选您需要的联赛与时段查看深层胜率。")

st.title("⚽ 赛事盘口及跨天胜率分析系统")

# --- 1. 数据初始化 ---
if 'matches_df' not in st.session_state:
    if os.path.exists(MATCHES_FILE) and os.path.exists(ODDS_FILE):
        with open(MATCHES_FILE, 'rb') as f:
            st.session_state.matches_df = pickle.load(f)
        with open(ODDS_FILE, 'rb') as f:
            st.session_state.odds_data = pickle.load(f)
        if st.session_state.role == "admin":
            st.toast("读取本地存档成功！")
    else:
        # 如果连你也没有存档，给一个空表格框架
        st.session_state.matches_df = pd.DataFrame(columns=["日期", "星期", "联赛", "时间", "主队", "比分", "客队"])
        st.session_state.odds_data = {}

def get_single_handicap(): return pd.DataFrame([{"主水": "", "盘口": "", "客水": ""}])
def get_single_totals(): return pd.DataFrame([{"大球": "", "盘口": "", "小球": ""}])

def render_result_box(win_str, tag_str, water_val):
    html = f"""
    <div style='background-color: #fff3cd; color: #000000; padding: 8px; border-radius: 4px; border: 1px solid #ffeeba; margin-top: 5px; text-align: center;'>
        <strong>🎯 结算: {win_str} | {tag_str} (水位: {water_val})</strong>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# --- 2. 赛事列表编辑 ---
st.subheader("📋 1. 赛事总表")
# ⚡⚡⚡ 核心权限控制：Admin 是可编辑表格，Viewer 是纯展示表格 ⚡⚡⚡
if st.session_state.role == "admin":
    edited_matches = st.data_editor(st.session_state.matches_df, num_rows="dynamic", use_container_width=True, key="matches_editor")
    st.session_state.matches_df = edited_matches
else:
    st.dataframe(st.session_state.matches_df, use_container_width=True)
    edited_matches = st.session_state.matches_df # Viewers用现成的数据往下走

st.divider()

# --- 3. 跨天对比过滤引擎 ---
st.subheader("🎯 2. 盘口数据与对标分析")

edited_matches['日期展示'] = edited_matches['日期'].astype(str) + " (" + edited_matches['星期'].astype(str) + ")"
unique_dates = edited_matches['日期展示'].dropna().unique().tolist()
unique_dates.sort(reverse=True)

if unique_dates:
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        selected_dates_display = st.multiselect("📅 1. 选择要追踪对比的日期:", unique_dates, default=unique_dates)
        selected_dates = [d.split(" (")[0] for d in selected_dates_display]
        
    matches_at_date = edited_matches[edited_matches['日期'].isin(selected_dates)]
    
    with col_filter2:
        unique_times = matches_at_date['时间'].dropna().unique().tolist()
        unique_times.sort()
        selected_times = st.multiselect("⏰ 2. 选择时间段:", unique_times, default=unique_times)

    final_matches = matches_at_date[matches_at_date['时间'].isin(selected_times)]
    
    stats = {'hc': {'high': 0, 'low': 0, 'even': 0}, 'ou': {'high': 0, 'low': 0, 'even': 0}}
    match_results_log = [] 

    if not final_matches.empty:
        total_matches_count = len(final_matches)
        
        with st.container():
            for index, row in final_matches.iterrows():
                match_name = f"{row['主队']} vs {row['客队']}"
                
                with st.expander(f"📌 {row['日期']} {row['时间']} | {match_name} ({row['联赛']} | 比分: {row['比分']})", expanded=False):
                    if match_name not in st.session_state.odds_data:
                        st.session_state.odds_data[match_name] = {"handicap": get_single_handicap(), "totals": get_single_totals()}
                    match_odds = st.session_state.odds_data[match_name]
                    
                    score_str = str(row['比分'])
                    valid_score = False
                    try:
                        home_score, away_score = map(int, score_str.split('-'))
                        total_goals = home_score + away_score
                        valid_score = True
                    except: pass

                    col_in1, col_in2 = st.columns(2)
                    
                    hc_tag = None
                    with col_in1:
                        st.caption("🔴 让球")
                        # ⚡⚡⚡ 核心权限控制：只有 admin 才能填空 ⚡⚡⚡
                        if st.session_state.role == "admin":
                            edited_hc = st.data_editor(match_odds["handicap"], use_container_width=True, key=f"hc_{match_name}", hide_index=True)
                            st.session_state.odds_data[match_name]["handicap"] = edited_hc
                        else:
                            edited_hc = match_odds["handicap"]
                            st.dataframe(edited_hc, use_container_width=True, hide_index=True)
                        
                        if valid_score and not edited_hc.empty:
                            try:
                                h_w, line, a_w = float(edited_hc.iloc[0]["主水"]), float(edited_hc.iloc[0]["盘口"]), float(edited_hc.iloc[0]["客水"])
                                net_score = home_score - line - away_score
                                
                                if net_score > 0: win_str, winner = ("主队赢全" if net_score >= 0.5 else "主队赢半"), "home"
                                elif net_score < 0: win_str, winner = ("客队赢全" if net_score <= -0.5 else "客队赢半"), "away"
                                else: win_str, winner = "走水退本", "tie"
                                
                                high_side = "home" if h_w > a_w else "away" if h_w < a_w else "even"
                                hit_water = h_w if winner == "home" else a_w
                                opp_water = a_w if winner == "home" else h_w
                                
                                if winner == "tie":
                                    result_tag, water_display = "走水不计入", "-"
                                else:
                                    water_display = str(hit_water)
                                    if hit_water > opp_water: result_tag = "高水方打出"; stats['hc']['high'] += 1; hc_tag = 'high'
                                    elif hit_water < opp_water: result_tag = "低水方打出"; stats['hc']['low'] += 1; hc_tag = 'low'
                                    else: result_tag = "平水方打出"; stats['hc']['even'] += 1; hc_tag = 'even'
                                        
                                render_result_box(win_str, result_tag, water_display)
                            except: pass
                    
                    ou_tag = None
                    with col_in2:
                        st.caption("🔵 大小球")
                        if st.session_state.role == "admin":
                            edited_tot = st.data_editor(match_odds["totals"], use_container_width=True, key=f"tot_{match_name}", hide_index=True)
                            st.session_state.odds_data[match_name]["totals"] = edited_tot
                        else:
                            edited_tot = match_odds["totals"]
                            st.dataframe(edited_tot, use_container_width=True, hide_index=True)
                        
                        if valid_score and not edited_tot.empty:
                            try:
                                o_w, line, u_w = float(edited_tot.iloc[0]["大球"]), float(edited_tot.iloc[0]["盘口"]), float(edited_tot.iloc[0]["小球"])
                                net_goals = total_goals - line
                                
                                if net_goals > 0: win_str, winner = ("大球全赢" if net_goals >= 0.5 else "大球赢半"), "over"
                                elif net_goals < 0: win_str, winner = ("小球全赢" if net_goals <= -0.5 else "小球赢半"), "under"
                                else: win_str, winner = "走水退本", "tie"
                                
                                high_side = "over" if o_w > u_w else "under" if o_w < u_w else "even"
                                hit_water = o_w if winner == "over" else u_w
                                opp_water = u_w if winner == "over" else o_w
                                
                                if winner == "tie":
                                    result_tag, water_display = "走水不计入", "-"
                                else:
                                    water_display = str(hit_water)
                                    if hit_water > opp_water: result_tag = "高水方打出"; stats['ou']['high'] += 1; ou_tag = 'high'
                                    elif hit_water < opp_water: result_tag = "低水方打出"; stats['ou']['low'] += 1; ou_tag = 'low'
                                    else: result_tag = "平水方打出"; stats['ou']['even'] += 1; ou_tag = 'even'
                                
                                render_result_box(win_str, result_tag, water_display)
                            except: pass
                            
                    match_results_log.append({
                        "日期": row['日期'],
                        "时间": row['时间'],
                        "联赛": row['联赛'],
                        "hc_tag": hc_tag,
                        "ou_tag": ou_tag
                    })

        st.divider()
        
        # ========================================================
        # 终极杀器：全能组合式 底牌追踪器
        # ========================================================
        st.subheader(f"📈 每天同时间/同联赛 - 庄家底牌追踪器")
        
        log_df = pd.DataFrame(match_results_log)
        
        if not log_df.empty:
            
            options = ["🌍 全盘汇总 (当前选中的所有时间+所有联赛)"]
            
            unique_times = sorted(log_df['时间'].unique().tolist())
            for t in unique_times:
                options.append(f"⏰ 时间汇总: {t} | 所有联赛")
                
            log_df['赛道'] = log_df['时间'] + " | " + log_df['联赛']
            unique_tracks = sorted(log_df['赛道'].unique().tolist())
            for t in unique_tracks:
                options.append(f"🎯 独立赛道: {t}")
            
            selected_option = st.selectbox("👇 请选择追踪维度 (看总盘概率 还是 独立联赛):", options)
            
            if selected_option == "🌍 全盘汇总 (当前选中的所有时间+所有联赛)":
                track_df = log_df
                display_title = "全部选中赛事"
            elif selected_option.startswith("⏰ 时间汇总:"):
                target_time = selected_option.split("时间汇总: ")[1].split(" |")[0]
                track_df = log_df[log_df['时间'] == target_time]
                display_title = f"[{target_time}] 所有联赛汇总"
            else:
                target_track = selected_option.replace("🎯 独立赛道: ", "")
                track_df = log_df[log_df['赛道'] == target_track]
                display_title = f"[{target_track}] 独立数据"
            
            table_data = []
            hc_chart_data = []
            ou_chart_data = []
            
            for date, group in track_df.groupby("日期"):
                hc_h = (group['hc_tag'] == 'high').sum()
                hc_l = (group['hc_tag'] == 'low').sum()
                hc_e = (group['hc_tag'] == 'even').sum()
                hc_valid = hc_h + hc_l + hc_e
                
                ou_h = (group['ou_tag'] == 'high').sum()
                ou_l = (group['ou_tag'] == 'low').sum()
                ou_e = (group['ou_tag'] == 'even').sum()
                ou_valid = ou_h + ou_l + ou_e
                
                total_matches = len(group)
                
                table_data.append({
                    "日期": date,
                    "总场次": total_matches,
                    "🔴高水(场)": hc_h,
                    "🔴低水(场)": hc_l,
                    "🔴高水胜率": f"{hc_h/hc_valid*100:.1f}%" if hc_valid > 0 else "-",
                    "🔴低水胜率": f"{hc_l/hc_valid*100:.1f}%" if hc_valid > 0 else "-",
                    "🔵高水(场)": ou_h,
                    "🔵低水(场)": ou_l,
                    "🔵高水率": f"{ou_h/ou_valid*100:.1f}%" if ou_valid > 0 else "-",
                    "🔵低水率": f"{ou_l/ou_valid*100:.1f}%" if ou_valid > 0 else "-"
                })
                
                hc_chart_data.append({"日期": date, "🔥高水赢盘(场)": hc_h, "🧊低水赢盘(场)": hc_l})
                ou_chart_data.append({"日期": date, "🔥高水打出(场)": ou_h, "🧊低水打出(场)": ou_l})
                
            st.dataframe(pd.DataFrame(table_data).set_index("日期"), use_container_width=True)
            
            hc_df = pd.DataFrame(hc_chart_data).set_index("日期")
            ou_df = pd.DataFrame(ou_chart_data).set_index("日期")
            
            if len(hc_df) > 0:
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    st.markdown(f"**{display_title} 👉 🔴让球：每天高低水场次**")
                    st.bar_chart(hc_df, color=["#ff4b4b", "#1f77b4"])
                with col_t2:
                    st.markdown(f"**{display_title} 👉 🔵大小球：每天高低水场次**")
                    st.bar_chart(ou_df, color=["#ff4b4b", "#1f77b4"])
            else:
                st.info("⚠️ 所选维度下，暂无包含高低水胜负的有效数据。")

else:
    st.info("尚未录入比赛。")