from model import *

text = input("enter the text\n")

s = output(text)

print(ranking(s))


# def priority(t):
#     fs = ranking(s)
#     if fs >= 0.7900:
#         print("the authour says its really urgent")


print(predict_category(text))
