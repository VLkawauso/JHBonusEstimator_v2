import streamlit as st

# --- ロジック部分 ---
def calculate_expressiveness_score(intonation_raw, technique_raw):
    """抑揚と技法点の実数値から表現力スコアを算出する。"""
    intonation_axis = [0.0, 45.0, 70.0, 80.0, 90.0, 100.0]
    technique_axis = [0.0, 40.0, 60.0, 80.0, 90.0, 100.0]
    score_grid = [
        [0, 30000, 40000, 50000, 53000, 55000],
        [30000, 50000, 65000, 78000, 82000, 83500],
        [50000, 63000, 75000, 86000, 88500, 92000],
        [56000, 66000, 80000, 89000, 92500, 95000],
        [60000, 68000, 82000, 93100, 95000, 97500],
        [63000, 70000, 84000, 95000, 98000, 100000]
    ]
    
    def find_axis_index(value, axis):
        if value >= 100.0: return len(axis) - 2
        for i in range(len(axis) - 1):
            if axis[i] <= value < axis[i+1]: return i
        return len(axis) - 2

    idx_i = find_axis_index(intonation_raw, intonation_axis)
    idx_t = find_axis_index(technique_raw, technique_axis)
    intonation_ratio = (intonation_raw - intonation_axis[idx_i]) / (intonation_axis[idx_i+1] - intonation_axis[idx_i])
    technique_ratio = (technique_raw - technique_axis[idx_t]) / (technique_axis[idx_t+1] - technique_axis[idx_t])
    q11, q12, q21, q22 = score_grid[idx_i][idx_t], score_grid[idx_i][idx_t+1], score_grid[idx_i+1][idx_t], score_grid[idx_i+1][idx_t+1]
    return (1-intonation_ratio)*(1-technique_ratio)*q11 + intonation_ratio*(1-technique_ratio)*q21 + (1-intonation_ratio)*technique_ratio*q12 + intonation_ratio*technique_ratio*q22

def get_jh_count_from_bonus(target_bonus, accent_count):
    """
    画像の表に基づき、ボーナス値とアクセント数からJH数を逆算する。
    縦軸(JH): 0, 10, 20, 30, 40, 50
    横軸(ACC): 0, 10, 20, 30, 40, 50
    """
    jh_axis = [0, 10, 20, 30, 40, 50]
    acc_axis = [0, 10, 20, 30, 40, 50]
    # 表の内容
    bonus_table = [
        [0,  0,  0, 0, 0, 0], # JH 0
        [10, 5,  0, 0, 0, 0], # JH 10
        [20, 10, 5, 3, 2, 1], # JH 20
        [30, 20, 8, 4, 3, 2], # JH 30
        [40, 25, 9, 5, 3, 2], # JH 40
        [50, 30, 10, 5, 3, 2] # JH 50
    ]
    
    # 最近似のACCインデックスを探す
    acc_idx = min(range(len(acc_axis)), key=lambda i: abs(acc_axis[i] - accent_count))
    
    possible_jhs = []
    for i, jh_val in enumerate(jh_axis):
        if bonus_table[i][acc_idx] == target_bonus:
            possible_jhs.append(jh_val)
    return possible_jhs

def solve_possible_bonus_range(display_intonation, display_expressiveness, base_technique_points):
    """境界条件に基づき、合計技法点の範囲からボーナス範囲を類推する。"""
    intonation_min = display_intonation * 10
    intonation_max = min(display_intonation * 10 + 9, 1000)
    expressiveness_min = display_expressiveness * 1000
    expressiveness_max = min(display_expressiveness * 1000 + 999, 100000)
    
    min_total_t = None
    for t in range(0, 1251):
        if calculate_expressiveness_score(intonation_max / 10.0, t / 12.5) >= expressiveness_min:
            min_total_t = t
            break
    max_total_t = None
    for t in range(1250, -1, -1):
        if calculate_expressiveness_score(intonation_min / 10.0, t / 12.5) <= expressiveness_max:
            max_total_t = t
            break

    if min_total_t is None or max_total_t is None or min_total_t > max_total_t:
        return []

    possible_bonuses = []
    for t in range(min_total_t, max_total_t + 1):
        bonus = t - base_technique_points
        if bonus >= 0:
            possible_bonuses.append(bonus)
    return sorted(list(set(possible_bonuses)))

# --- Streamlit UI ---
st.set_page_config(page_title="JH Bonus Analyzer", page_icon="🎯")
st.title("💥 ジャストヒットボーナス解析")

analysis_mode = st.radio("解析精度を選択", ("【予測】みかけの数値から推定する", "【正確】実数値から特定する"), horizontal=True)
st.divider()

if analysis_mode == "【予測】みかけの数値から推定する":
    st.subheader("🔍 みかけ数値推定モード")
    col_i, col_s = st.columns(2)
    with col_i: input_disp_i = st.number_input("みかけの抑揚 (0-100)", 0, 100, 99)
    with col_s: input_disp_s = st.number_input("みかけの表現力 (0-100)", 0, 100, 99)
    
    col_base, col_acc = st.columns(2)
    with col_base: input_base_t = st.number_input("基礎技法点 (0-1250)", 0, 1250, 800)
    with col_acc: input_acc = st.number_input("アクセント数 (0-50)", 0, 50, 0, step=10)

    if st.button("範囲を類推する", type="primary", use_container_width=True):
        bonus_results = solve_possible_bonus_range(input_disp_i, input_disp_s, input_base_t)
        if bonus_results:
            b_min, b_max = min(bonus_results), max(bonus_results)
            st.success("解析完了")
            
            # ボーナス結果表示
            if b_min == b_max:
                st.metric("確定ボーナス値", f"{b_min} 点")
            else:
                st.subheader(f"ボーナス推定範囲: {b_min} ～ {b_max} 点")
            
            # JH数の類推オプション
            st.info(f"💡 アクセント数 {input_acc} の時のJH数類推")
            all_possible_jhs = []
            for b in bonus_results:
                all_possible_jhs.extend(get_jh_count_from_bonus(b, input_acc))
            
            unique_jhs = sorted(list(set(all_possible_jhs)))
            if unique_jhs:
                st.write(f"該当する可能性のあるJH数: **{', '.join(map(str, unique_jhs))}**")
            else:
                st.write("表のデータ範囲内に該当するJH数はありませんでした。")
        else:
            st.error("条件に合うボーナスが見つかりませんでした。")

else:
    st.subheader("📋 詳細リザルト解析モード")
    col_ri, col_rs = st.columns(2)
    with col_ri: input_real_i = st.number_input("実際の抑揚 (0-1000)", 0, 1000, 990)
    with col_rs: input_real_s = st.number_input("実際の表現力 (0-100000)", 0, 100000, 99750)
    
    col_rb, col_ra = st.columns(2)
    with col_rb: input_base_t_precise = st.number_input("基礎技法点 (0-1250)", 0, 1250, 800)
    with col_ra: input_acc_precise = st.number_input("アクセント数 (0-50)", 0, 50, 0, step=10)

    if st.button("ボーナスを特定", type="primary", use_container_width=True):
        best_t, min_diff = 0, float('inf')
        for t in range(0, 1251):
            diff = abs(calculate_expressiveness_score(input_real_i / 10.0, t / 12.5) - input_real_s)
            if diff < min_diff: min_diff, best_t = diff, t
        
        bonus = best_t - input_base_t_precise
        if bonus < 0: st.error("基礎点が合計値を上回っています。")
        else:
            st.success("解析完了")
            st.metric("ジャストヒットボーナス", f"{bonus} 点")
            
            # JH数の逆算
            jhs = get_jh_count_from_bonus(bonus, input_acc_precise)
            if jhs:
                st.write(f"類推されるJH数: **{', '.join(map(str, jhs))}**")
            else:
                st.caption("※表のデータ範囲外のためJH数は類推できませんでした。")

st.divider()
st.caption("© 2026 Zawasow_lab")