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

def judge_result(score_a, score_b, label_a, label_b, epsilon=1e-9):
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

    # 2. MAC 연산 수행
    score_a = calculate_mac(pattern, filter_a)
    score_b = calculate_mac(pattern, filter_b)

    # 3. 결과 출력
    print("\n#---------------------------------------")
    print("# [3] MAC 결과")
    print("#---------------------------------------")
    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")

    # 4. 판정 (부동소수점 오차 고려 epsilon 적용)
    result = judge_result(score_a, score_b, "A", "B")
    print(f"판정: {result}\n")

def run_json_analysis_mode():
    # 1. JSON 파일 읽기
    # 2. 필터 로드 및 정규화
    # 3. 패턴들 하나씩 꺼내서 MAC 연산
    # 4. PASS/FAIL 판정 및 결과 요약 출력
    pass 

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