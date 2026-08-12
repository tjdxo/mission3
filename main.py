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

def main():
    print("=== Mini NPU Simulator (1단계) ===")
    
    # 1. 입력 받기 (3x3 기준)
    size = 3
    filter_a = get_matrix_input(size, "필터 A")
    filter_b = get_matrix_input(size, "필터 B")
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
    epsilon = 1e-9
    if abs(score_a - score_b) < epsilon:
        print("판정: 판정 불가 (동점)")
    elif score_a > score_b:
        print("판정: A")
    else:
        print("판정: B")

if __name__ == "__main__":
    main()