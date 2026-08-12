import json
import time


EPSILON = 1e-9
DEFAULT_REPEAT_COUNT = 10

def calculate_mac(matrix_a, matrix_b):
    """
    두 행렬의 같은 위치 원소를 곱하고 누적합(MAC)을 계산합니다.
    """
    score = 0.0
    size = len(matrix_a)
    for i in range(size):
        for j in range(size):
            score += matrix_a[i][j] * matrix_b[i][j]
    return score

def measure_mac_pair(pattern, filter_a, filter_b, repeat=DEFAULT_REPEAT_COUNT):
    """MAC 연산 수행 및 시간을 반복 측정하여 평균 소요 시간을 계산합니다."""
    score_a, score_b = 0.0, 0.0
    start = time.perf_counter()

    for _ in range(repeat):
        score_a = calculate_mac(pattern, filter_a)
        score_b = calculate_mac(pattern, filter_b)

    elapsed_ms = (time.perf_counter() - start) * 1000
    return score_a, score_b, elapsed_ms / repeat

def get_matrix_input(size, label):
    """
    사용자로부터 n x n 행렬 입력을 안전하게 받습니다.
    """
    print(f"\n{label} ({size}줄 입력, 공백 구분):")
    matrix = []
    while len(matrix) < size:
        try:
            line = input().split()
            # 입력 개수 검증
            if len(line) != size:
                print(f"입력 형식 오류: {size}개의 숫자를 공백으로 구분해 입력하세요.")
                continue
            
            # 숫자 변환 검증
            row = [float(x) for x in line]
            matrix.append(row)
        except ValueError:
            print("입력 형식 오류: 숫자만 입력 가능합니다.")
            
    return matrix

def judge_result(score_a, score_b, label_a, label_b, epsilon=EPSILON):
    """
    두 점수를 비교하여 승자 라벨 또는 'UNDECIDED'를 반환합니다.
    """
    if abs(score_a - score_b) < epsilon:
        return "UNDECIDED"
    elif score_a > score_b:
        return label_a
    else:
        return label_b

def normalize_label(label):
    label = str(label).lower() # 소문자로 통일
    if label in ['+', 'cross']:
        return "Cross"
    if label in ['x']:
        return "X"
    return "UNDECIDED"

def load_data():
    try:
        with open('data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("data.json 파일을 찾을 수 없습니다.")
        return None
    
def process_case(p_id, p_info, filters):
    """패턴 하나를 분석하여 점수, 판정 결과, 소요 시간을 반환합니다."""
    pattern_matrix = p_info.get("input")
    expected_norm = normalize_label(p_info.get("expected"))
    
    # 키 추출 (size_5_1 -> size_5)
    size_key = "_".join(p_id.split("_")[:2])
    current_filters = filters.get(size_key)

    if not current_filters:
        return None, f"필터 누락 ({size_key})"

    # MAC 연산 및 시간 측정 (10회 반복)
    f_cross = current_filters.get("cross")
    f_x = current_filters.get("x")
    
    start = time.perf_counter()
    for _ in range(DEFAULT_REPEAT_COUNT):
        score_cross = calculate_mac(pattern_matrix, f_cross)
        score_x = calculate_mac(pattern_matrix, f_x)
    avg_time = ((time.perf_counter() - start) / DEFAULT_REPEAT_COUNT) * 1000

    # 판정
    result = judge_result(score_cross, score_x, "Cross", "X")
    is_pass = (result == expected_norm)
    
    return {
        "id": p_id,
        "size_key": size_key,
        "scores": (score_cross, score_x),
        "result": result,
        "expected": expected_norm,
        "is_pass": is_pass,
        "time": avg_time,
        "n_squared": len(pattern_matrix)**2
    }, None

def print_performance_report(perf_data):
    print("\n#---------------------------------------")
    print("# [3] 성능 분석 (평균/10회)")
    print("#---------------------------------------")
    print(f"{'크기':<10} {'평균 시간(ms)':<15} {'연산 횟수(N²)'}")
    print("-" * 45)
    for size in sorted(perf_data.keys(), key=lambda x: int(x.split('_')[1])):
        d = perf_data[size]
        n = size.split('_')[1]
        print(f"{n+'x'+n:<10} {d['time']:<15.6f} {d['ops']}")

def print_final_summary(stats):
    print("\n#---------------------------------------")
    print("# [4] 결과 요약")
    print("#---------------------------------------")
    print(f"총 테스트: {stats['total']}개 | 통과: {stats['pass']}개 | 실패: {stats['fail']}개")
    if stats['fail_cases']:
        print("\n실패 케이스:")
        for case in stats['fail_cases']:
            print(f"- {case}")

def run_user_input_mode():
    # 1. 입력 받기 (3x3 기준)
    print("\n#---------------------------------------")
    print("# [1] 필터 입력")
    print("#---------------------------------------")
    size = 3
    filter_a = get_matrix_input(size, "필터 A")
    filter_b = get_matrix_input(size, "필터 B")

    print("\n#---------------------------------------")
    print("# [2] 패턴 입력")
    print("#---------------------------------------")
    pattern = get_matrix_input(size, "패턴")

    # 2. MAC 연산 수행 및 판정
    score_a, score_b, avg_time = measure_mac_pair(pattern, filter_a, filter_b)
    result = judge_result(score_a, score_b, "A", "B")


    # 3. 결과 출력
    print("\n#---------------------------------------")
    print("# [3] MAC 결과")
    print("#---------------------------------------")
    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/10회): {avg_time:.6f} ms")
    print(f"판정: {'판정 불가 (|A-B| < 1e-9)' if result == 'UNDECIDED' else result}")
    
def run_json_analysis_mode():
    data = load_data()
    if not data: return

    filters = data.get("filters", {})
    patterns = data.get("patterns", {})
    
    stats = {"total": 0, "pass": 0, "fail": 0, "fail_cases": []}
    perf_summary = {}

    print("\n# [1] 필터 로드 완료")
    print("# [2] 패턴 분석 시작")

    for p_id, p_info in patterns.items():
        res, error = process_case(p_id, p_info, filters)
        
        if error:
            stats["fail"] += 1
            stats["fail_cases"].append(f"{p_id}: {error}")
            continue

        # 결과 출력 및 통계 합산
        stats["total"] += 1
        if res["is_pass"]: stats["pass"] += 1
        else: 
            stats["fail"] += 1
            stats["fail_cases"].append(f"{res['id']}: 판정 {res['result']} != 기대 {res['expected']}")

        print(f"--- {res['id']} ---")
        print(f"Cross: {res['scores'][0]:.4f} | X: {res['scores'][1]:.4f}")
        print(f"판정: {res['result']} | {'PASS' if res['is_pass'] else 'FAIL'}")

        # 성능 데이터 저장 (크기별 마지막 측정값 기준 또는 평균)
        perf_summary[res['size_key']] = {"time": res['time'], "ops": res['n_squared']}

    # 분석 결과 출력
    print_performance_report(perf_summary)
    print_final_summary(stats)

def main():
    print("=== Mini NPU Simulator===")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")
    
    choice = input("선택: ")

    if choice == '1':
        # 이전에 만든 모드 1 로직 실행
        run_user_input_mode()
    elif choice == '2':
        # 이제 만들어야 할 모드 2 로직 실행
        run_json_analysis_mode()
    else:
        print("잘못된 선택입니다.")

if __name__ == "__main__":
    main()