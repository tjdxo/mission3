import json
import time


EPSILON = 1e-9
DEFAULT_REPEAT_COUNT = 10
DATA_FILE = "data.json"
VALID_RESULT_LABELS = {"Cross", "X"}


# =========================
# 유틸 함수
# =========================
def normalize_label(label):
    """입력 라벨을 내부 표준 라벨(Cross, X)로 정규화합니다."""
    label = str(label).strip().lower()
    if label in ["+", "cross"]:
        return "Cross"
    if label == "x":
        return "X"
    return None


def parse_size_key(size_key):
    """size_5 같은 키에서 숫자 크기를 추출합니다."""
    parts = size_key.split("_")
    if len(parts) != 2 or parts[0] != "size" or not parts[1].isdigit():
        return None
    return int(parts[1])


def parse_pattern_size(pattern_id):
    """size_5_1 같은 패턴 키에서 행렬 크기를 추출합니다."""
    parts = pattern_id.split("_")
    if len(parts) != 3:
        return None
    if parts[0] != "size" or not parts[1].isdigit() or not parts[2].isdigit():
        return None
    return int(parts[1])


def get_size_sort_key(size_key):
    """size_N 형식 키를 숫자 기준으로 정렬하기 위한 키를 반환합니다."""
    size = parse_size_key(size_key)
    return size if size is not None else 9999


def get_pattern_sort_key(pattern_id):
    """size_N_idx 패턴 키를 크기/인덱스 기준으로 정렬하기 위한 키를 반환합니다."""
    parts = pattern_id.split("_")
    if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
        return int(parts[1]), int(parts[2])
    return 9999, 9999


def calculate_mac(matrix_a, matrix_b):
    """두 행렬의 같은 위치 원소를 곱하고 누적합(MAC)을 계산합니다."""
    score = 0.0
    size = len(matrix_a)

    for i in range(size):
        for j in range(size):
            score += matrix_a[i][j] * matrix_b[i][j]

    return score


def measure_mac_pair(pattern, filter_a, filter_b, repeat=DEFAULT_REPEAT_COUNT):
    """두 필터에 대한 MAC 점수와 평균 연산 시간을 측정합니다."""
    score_a = 0.0
    score_b = 0.0
    start = time.perf_counter()

    for _ in range(repeat):
        score_a = calculate_mac(pattern, filter_a)
        score_b = calculate_mac(pattern, filter_b)

    elapsed_ms = (time.perf_counter() - start) * 1000
    return score_a, score_b, elapsed_ms / repeat


def judge_result(score_a, score_b, label_a, label_b, epsilon=EPSILON):
    """두 점수를 비교하여 승자 라벨 또는 UNDECIDED를 반환합니다."""
    if abs(score_a - score_b) < epsilon:
        return "UNDECIDED"
    if score_a > score_b:
        return label_a
    return label_b


def get_matrix_input(size, label):
    """사용자로부터 n x n 행렬 입력을 안전하게 받습니다."""
    print(f"\n{label} ({size}줄 입력, 공백 구분):")
    matrix = []

    while len(matrix) < size:
        try:
            line = input().split()

            if len(line) != size:
                print(f"입력 형식 오류: 각 줄에 {size}개의 숫자를 공백으로 구분해 입력하세요.")
                continue

            row = [float(x) for x in line]
            matrix.append(row)

        except ValueError:
            print("입력 형식 오류: 숫자만 입력 가능합니다.")

    return matrix


def add_perf_result(perf_summary, size_key, elapsed_time, ops):
    """크기별 성능 데이터를 수동 초기화 방식으로 저장합니다."""
    if size_key not in perf_summary:
        perf_summary[size_key] = {"times": [], "ops": 0}

    perf_summary[size_key]["times"].append(elapsed_time)
    perf_summary[size_key]["ops"] = ops


def add_builtin_3x3_perf(perf_summary):
    """JSON 모드 성능표에 포함할 3x3 내장 샘플 측정값을 추가합니다."""
    sample_cross = [
        [0.0, 1.0, 0.0],
        [1.0, 1.0, 1.0],
        [0.0, 1.0, 0.0]
    ]
    sample_x = [
        [1.0, 0.0, 1.0],
        [0.0, 1.0, 0.0],
        [1.0, 0.0, 1.0]
    ]
    sample_pattern = [
        [1.0, 0.0, 1.0],
        [0.0, 1.0, 0.0],
        [1.0, 0.0, 1.0]
    ]

    _, _, avg_time = measure_mac_pair(sample_pattern, sample_cross, sample_x)
    add_perf_result(perf_summary, "size_3", avg_time, 9)


# =========================
# 검증 함수
# =========================
def validate_matrix(matrix, expected_size=None, name="matrix"):
    """행렬이 올바른 2차원 숫자 정사각형 배열인지 검증합니다."""
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


def validate_pattern_info(pattern_id, pattern_info):
    """패턴 항목의 키/입력 행렬/expected 값을 검증합니다."""
    if not isinstance(pattern_info, dict):
        return None, None, "패턴 정보가 객체(dict) 형태가 아닙니다."

    size = parse_pattern_size(pattern_id)
    if size is None:
        return None, None, f"패턴 키 형식 오류: {pattern_id}"

    if "input" not in pattern_info:
        return size, None, "input 누락"

    if "expected" not in pattern_info:
        return size, None, "expected 누락"

    matrix = pattern_info["input"]
    expected_norm = normalize_label(pattern_info["expected"])

    if expected_norm not in VALID_RESULT_LABELS:
        return size, None, f"expected 값 오류: {pattern_info['expected']}"

    matrix_error = validate_matrix(matrix, size, f"{pattern_id}.input")
    if matrix_error:
        return size, None, matrix_error

    return size, expected_norm, None


def normalize_filter_dict(filter_dict):
    """필터 키를 표준 라벨(Cross, X)로 정규화합니다."""
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
    """필터 전체를 검증하고 내부 표준 구조로 변환합니다."""
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


# =========================
# 로드 함수
# =========================
def load_data():
    """data.json 파일을 로드하고 루트 구조를 검증합니다."""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"{DATA_FILE} 파일을 찾을 수 없습니다.")
        return None
    except json.JSONDecodeError as error:
        print(
            f"{DATA_FILE} JSON 파싱 오류: "
            f"{error.msg} (line {error.lineno}, col {error.colno})"
        )
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


# =========================
# 분석 함수
# =========================
def process_case(pattern_id, pattern_info, filters):
    """패턴 하나를 검증/분석하여 점수, 판정 결과, 시간을 반환합니다."""
    size, expected_norm, pattern_error = validate_pattern_info(pattern_id, pattern_info)
    if pattern_error:
        return None, pattern_error

    size_key = f"size_{size}"
    current_filters = filters.get(size_key)

    if not current_filters:
        return None, f"필터 누락 ({size_key})"

    pattern_matrix = pattern_info["input"]
    cross_filter = current_filters["Cross"]
    x_filter = current_filters["X"]

    if len(pattern_matrix) != len(cross_filter) or len(pattern_matrix) != len(x_filter):
        return None, f"패턴/필터 크기 불일치 ({size_key})"

    score_cross, score_x, avg_time = measure_mac_pair(pattern_matrix, cross_filter, x_filter)
    result = judge_result(score_cross, score_x, "Cross", "X")
    is_pass = (result == expected_norm)

    return {
        "id": pattern_id,
        "size_key": size_key,
        "scores": (score_cross, score_x),
        "result": result,
        "expected": expected_norm,
        "is_pass": is_pass,
        "time": avg_time,
        "n_squared": len(pattern_matrix) ** 2
    }, None


# =========================
# 출력 / 실행 함수
# =========================
def print_performance_report(perf_data):
    print("\n#---------------------------------------")
    print("# [3] 성능 분석 (평균/10회)")
    print("#---------------------------------------")
    print(f"{'크기':<10} {'평균 시간(ms)':<15} {'연산 횟수(N²)'}")
    print("-" * 45)

    for size_key in sorted(perf_data.keys(), key=get_size_sort_key):
        data = perf_data[size_key]
        avg_time = sum(data["times"]) / len(data["times"]) if data["times"] else 0.0
        size = size_key.split("_")[1]
        print(f"{size + 'x' + size:<10} {avg_time:<15.6f} {data['ops']}")


def print_final_summary(stats):
    print("\n#---------------------------------------")
    print("# [4] 결과 요약")
    print("#---------------------------------------")
    print(f"총 테스트: {stats['total']}개 | 통과: {stats['pass']}개 | 실패: {stats['fail']}개")

    if stats["fail_cases"]:
        print("\n실패 케이스:")
        for case in stats["fail_cases"]:
            print(f"- {case}")


def run_user_input_mode():
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

    score_a, score_b, avg_time = measure_mac_pair(pattern, filter_a, filter_b)
    result = judge_result(score_a, score_b, "A", "B")

    print("\n#---------------------------------------")
    print("# [3] MAC 결과")
    print("#---------------------------------------")
    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/10회): {avg_time:.6f} ms")
    print(f"판정: {'판정 불가 (|A-B| < 1e-9)' if result == 'UNDECIDED' else result}")


def run_json_analysis_mode():
    data = load_data()
    if data is None:
        return

    raw_filters = data.get("filters", {})
    patterns = data.get("patterns", {})

    stats = {
        "total": 0,
        "pass": 0,
        "fail": 0,
        "fail_cases": []
    }
    perf_summary = {}

    validated_filters, filter_errors = validate_and_build_filters(raw_filters)

    print("\n#---------------------------------------")
    print("# [1] 필터 로드")
    print("#---------------------------------------")

    for size_key in sorted(raw_filters.keys(), key=get_size_sort_key):
        if size_key in validated_filters:
            print(f"✓ {size_key} 필터 로드 완료 (Cross, X)")
        else:
            print(f"✗ {size_key} 필터 로드 실패: {filter_errors.get(size_key, '알 수 없는 오류')}")

    print("\n#---------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#---------------------------------------")

    for pattern_id in sorted(patterns.keys(), key=get_pattern_sort_key):
        pattern_info = patterns[pattern_id]
        stats["total"] += 1

        result, error = process_case(pattern_id, pattern_info, validated_filters)

        if error:
            stats["fail"] += 1
            stats["fail_cases"].append(f"{pattern_id}: {error}")
            print(f"--- {pattern_id} ---")
            print(f"판정 불가 | FAIL | 사유: {error}")
            continue

        if result["is_pass"]:
            stats["pass"] += 1
        else:
            stats["fail"] += 1
            stats["fail_cases"].append(
                f"{result['id']}: 판정 {result['result']} != 기대 {result['expected']}"
            )

        print(f"--- {result['id']} ---")
        print(f"Cross 점수: {result['scores'][0]:.4f}")
        print(f"X 점수: {result['scores'][1]:.4f}")
        print(
            f"판정: {result['result']} | expected: {result['expected']} | "
            f"{'PASS' if result['is_pass'] else 'FAIL'}"
        )

        add_perf_result(
            perf_summary,
            result["size_key"],
            result["time"],
            result["n_squared"]
        )

    add_builtin_3x3_perf(perf_summary)
    print_performance_report(perf_summary)
    print_final_summary(stats)


def main():
    print("=== Mini NPU Simulator ===")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")

    choice = input("선택: ").strip()

    if choice == "1":
        run_user_input_mode()
    elif choice == "2":
        run_json_analysis_mode()
    else:
        print("잘못된 선택입니다.")


if __name__ == "__main__":
    main()