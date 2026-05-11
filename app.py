import streamlit as st
import numpy as np

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

def interpolate_jh_bonus(jh_count, accent_count):
    """
    画像のJHボーナス表に基づき、2次元線形補間でボーナス値を算出する。
    """
    jh_axis = [0.0, 10.0, 20.0, 30.0, 40.0, 50.0]
    acc_axis = [0.0, 10.0, 20.0, 30.0, 40.0, 50.0]
    bonus_table = [
        [0,  0,  0, 0, 0, 0], # JH 0
        [10, 5,  0, 0, 0, 0], # JH 10
        [20, 10, 5, 3, 2, 1], # JH 20
        [30, 20, 8, 4, 3, 2], # JH 30
        [40, 25, 9, 5, 3, 2], # JH 40
        [50, 30, 10, 5, 3, 2] # JH 50
    ]

    # 範囲外をクリップ
    jh_val = max(0.0, min(50.0, float(jh_count)))
    acc_val = max(0.0, min(50.0, float(accent_count)))

    # インデックス検索
    def get_idx(val, axis):
        for i in range(len(axis)-1):
            if axis[i] <= val <= axis[i+1]: return i
        return len(axis)-2

    i, j = get_idx(jh_val, jh_axis), get_idx(acc_val, acc_axis)
    
    # 割合
    r_jh = (jh_val - jh_axis[i]) / (jh_axis[i+1] - jh_axis[i])
    r_acc = (acc_val - acc_axis[j]) / (acc_axis[j+1] - acc_axis[j])

    # 4点補間
    b11, b12, b21, b22 = bonus_table[i][j], bonus_table[i][j+1], bonus_table[i+1][j], bonus_table[i+1][j+1]
    
    return (1-r_jh)*(1-r_acc)*b11 + r_jh*(1-r_acc)*b21 + (1-r_jh)*r_acc*b12 + r_jh*r_acc*b22

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
    with col_acc: input_acc = st.number_input("アクセント数 (実数値可)", 0.0, 50.0, 0.0)

    if st.button("範囲を類推する", type="primary", use_container_width=True):
        bonus_results = solve_possible_bonus_range(input_disp_i, input_disp_s, input_base_t)
        if bonus_results:
            b_min, b_max = min(bonus_results), max(bonus_results)
            st.success("解析完了")
            
            if b_min == b_max: st.metric("確定ボーナス値", f"{b_min} 点")
            else: st.subheader(f"ボーナス推定範囲: {b_min} ～ {b_max} 点")
            
            # JH数の補間逆算
            st.info(f"💡 アクセント数 {input_acc} の時のJH数類推 (線形補間)")
            jh_results = []
            # JH 0.0から50.0まで0.1刻みで探索
            for test_jh in np.arange(0.0, 50.1, 0.1):
                calc_b = interpolate_jh_bonus(test_jh, input_acc)
                # 推定されたボーナス範囲のいずれかと一致（誤差許容）するか確認
                if any(abs(calc_b - b) < 0.2 for b in bonus_results):
                    jh_results.append(round(test_jh, 1))
            
            if jh_results:
                jh_min, jh_max = min(jh_results), max(jh_results)
                if jh_min == jh_max: st.write(f"該当するJH数: **{jh_min}**")
                else: st.write(f"該当するJH数範囲: **{jh_min} ～ {jh_max}**")
            else:
                st.write("表のデータ範囲内に該当するJH数は見つかりませんでした。")
        else:
            st.error("条件に合うボーナスが見つかりませんでした。")

else:
    st.subheader("📋 詳細リザルト解析モード")
    col_ri, col_rs = st.columns(2)
    with col_ri: input_real_i = st.number_input("実際の抑揚 (0-1000)", 0, 1000, 990)
    with col_rs: input_real_s = st.number_input("実際の表現力 (0-100000)", 0, 100000, 99750)
    
    col_rb, col_ra = st.columns(2)
    with col_rb: input_base_t_precise = st.number_input("基礎技法点 (0-1250)", 0, 1250, 800)
    with col_ra: input_acc_precise = st.number_input("アクセント数 (実数値可)", 0.0, 50.0, 0.0)

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
            
            # 補間によるJH数の特定（全探索）
            jh_candidates = []
            for test_jh in np.arange(0.0, 50.1, 0.1):
                if abs(interpolate_jh_bonus(test_jh, input_acc_precise) - bonus) < 0.2:
                    jh_candidates.append(round(test_jh, 1))
            
            if jh_candidates:
                st.write(f"推定されるJH数: **{min(jh_candidates)} ～ {max(jh_candidates)}**")

st.divider()
st.caption("© 2026 Zawasow_lab")