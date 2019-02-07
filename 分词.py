import jieba

a = '我有一个苹果园'
b = jieba.cut_for_search(a)
for bb in b:
    print(bb)
