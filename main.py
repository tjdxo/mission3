import json
import time
from collections import defaultdict

EPSILON = 1e-9
DEFAULT_REPEAT_COUNT = 10
DATA_FILE = "data.json"
VALID_RESULT_LABELS = {"Cross", "X"}

def parse_size_key(size_key):
    parts = size_key.split("_")
    if len(parts) != 2 or parts[0] != "size" or not parts[1].isdigit():
        return None
    return int(parts[1])

def parse_pattern_size(p_id):
    parts = p_id.split("_")
    if len(parts) != 3 or parts[0] != "size" or not parts[1].isdigit() or not parts[2].isdigit():
        return None
    return int(parts[1])

def validate_matrix(matrix, expected_size=None, name="matrix"):
    if not isinstance(matrix, list) or not matrix:
        return f"{name}: 비어 있지 않은 2차원 배열이어야 합니다."

    row_count = len(matrix)

    if expected_size is not None and row_count != expected_size:
        return f"{name}: 행 수가 {expected_size}가 아닙니다. (현재 {row_count})"

    for i, row in enumerate(matrix):
        if not isinstance(row, list):
            return f"{name}: {i}번 행이 리스트가 아닙니다."

        col_count = len(row)

        if expected_size is not None:
            if col_count != expected_size:
                return f"{name}: {i}번 행의 열 수가 {expected_size}가 아닙니다. (현재 {col_count})"
        else:
            if col_count != row_count:
                return f"{name}: 정사각형 행렬이 아닙니다. ({row_count}x{col_count})"

        for j, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return f"{name}: ({i}, {j}) 값이 숫자가 아닙니다."

    return None

def validate_pattern_info(p_id, p_info):
    if not isinstance(p_info, dict):
        return None, None, "패턴 정보가 객체(dict) 형태가 아닙니다."

    size = parse_pattern_size(p_id)
    if size is None:
        return None, None, f"패턴 키 형식 오류: {p_id}"

    if "input" not in p_info:
        return size, None, "input 누락"
    if "expected" not in p_info:
        return size, None, "expected 누락"

    matrix = p_info["input"]
    expected_norm = normalize_label(p_info["expected"])

    if expected_norm not in VALID_RESULT_LABELS:
        return size, None, f"expected 값 오류: {p_info['expected']}"

    matrix_error = validate_matrix(matrix, size, f"{p_id}.input")
    if matrix_error:
        return size, None, matrix_error

    return size, expected_norm, None

def calculate_mac(matrix_a, matrix_b):
    """두 행렬의 같은 위치 원소를 곱하고 누적합(MAC)을 계산합니다."""
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
    """사용자로부터 n x n 행렬 입력을 안전하게 받습니다."""
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
    """두 점수를 비교하여 승자 라벨 또는 'UNDECIDED'를 반환합니다."""
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
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"{DATA_FILE} 파일을 찾을 수 없습니다.")
        return None
    except json.JSONDecodeError as e:
        print(f"{DATA_FILE} JSON 파싱 오류: {e.msg} (line {e.lineno}, col {e.colno})")
        return None

    if not isinstance(data, dict):
        print("data.json 루트는 객체(dict)여야 합니다.")
        return None

    if not isinstance(data.get("filters"), dict):
        print("data.json의 filters는 객체(dict)여야 합니다.")
        return None

    if not isinstance(data.get("patterns"), dict):
        print("data.json의 patterns는 객체(dict)여야 합니다.")
        return None

    return data

def normalize_filter_dict(filter_dict):
    """필터 키를 표준 라벨(Cross, X)로 정규화하고 필수 필터 존재 여부를 검증합니다."""
    if not isinstance(filter_dict, dict):
        return None, "필터 정보가 객체(dict) 형태가 아닙니다."

    normalized = {}

    for key, value in filter_dict.items():
        label = normalize_label(key)
        if label in ["Cross", "X"]:
            normalized[label] = value

    if "Cross" not in normalized:
        return None, "Cross 필터가 없습니다."
    if "X" not in normalized:
        return None, "X 필터가 없습니다."

    return normalized, None

def validate_and_build_filters(raw_filters):
    validated_filters = {}
    filter_errors = {}

    for size_key, filter_dict in raw_filters.items():
        size = parse_size_key(size_key)
        if size is None:
            filter_errors[size_key] = f"필터 키 형식 오류: {size_key}"
            continue

        normalized_filters, error = normalize_filter_dict(filter_dict)
        if error:
            filter_errors[size_key] = error
            continue

        cross_error = validate_matrix(normalized_filters["Cross"], size, f"{size_key}.Cross")
        if cross_error:
            filter_errors[size_key] = cross_error
            continue

        x_error = validate_matrix(normalized_filters["X"], size, f"{size_key}.X")
        if x_error:
            filter_errors[size_key] = x_error
            continue

        validated_filters[size_key] = normalized_filters

    return validated_filters, filter_errors

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

    score_cross, score_x, avg_time = measure_mac_pair(pattern_matrix, f_cross, f_x)

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

    print("\n#---------------------------------------")
    print("# [1] 필터 로드")
    print("#---------------------------------------")
    for size_key in sorted(filters.keys(), key=lambda x: int(x.split("_")[1])):
        _, error = normalize_filter_dict(filters[size_key])
        if error:
            print(f"✗ {size_key} 필터 로드 실패: {error}")
        else:
            print(f"✓ {size_key} 필터 로드 완료 (Cross, X)")

    print("\n#---------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#---------------------------------------")

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
        print(f"Cross 점수: {res['scores'][0]:.4f}")
        print(f"X 점수: {res['scores'][1]:.4f}")
        print(f"판정: {res['result']} | expected: {res['expected']} | {'PASS' if res['is_pass'] else 'FAIL'}")

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