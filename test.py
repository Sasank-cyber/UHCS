nc = input()
i = nc.split(" ")
k = int(i[1])
n = int(i[0])

scores = input()
l = [int(i) for i in scores.split(" ")]
pass_score =  l[k-1]
ans = [i for i in l if i>=pass_score and i!=0]
print(len(ans))
