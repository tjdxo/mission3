
a = input().split()
mac1 = [a]
for i in range(len(a) - 1):
    k = input().split()
    mac1.append(k)

print(mac1)

mac2 = []

for i in range(len(a)):
    k = input().split()
    mac2.append(k)

print(mac2)

s = 0

for i in range(len(mac1)):
    for j in range(len(mac1[i])):
        print(mac1[i][j], " * ", mac2[i][j], " = ",  int(mac1[i][j]) * int(mac2[i][j]))
        s += int(mac1[i][j]) * int(mac2[i][j])
        print("현재 s 는? ", s)


print(s)