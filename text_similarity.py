# Author : Alex Ksikes

def vector(txt):
    v = {}
    tokens = txt.split()
    for t in tokens:
        if v.has_key(t):
            v[t] +=1
        else:
            v[t] = 1
    return v

def dot(v1, v2):
    res = 0
    for a in v1:
        if v2.has_key(a):
            res += v1[a] * v2[a]
    return res

def score(txt1, txt2):
    return 1.0 * dot(vector(txt1), vector(txt2)) / max(len(txt1.split()), len(txt2.split()))

def most_similar(txt1, txt_list):
    v1 = vector(txt1)
    best_txt = ""
    best_score = -1
    for txt in txt_list:
        v2 = vector(txt)
        score = dot(v1, v2)
        if score > best_score:
            best_score = score
            best_txt = txt
    return best_txt
    
import sys
if __name__ == '__main__':
    if len(sys.argv) == 1:
        print 'Usage: python text_similarity.py text1 text2'
    else:
        print score(sys.argv[1], sys.argv[2])    
