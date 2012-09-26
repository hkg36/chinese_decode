#-*-coding:utf-8-*-
import bsddb3
import os
import pickle
import scipy
import scipy.linalg

s = '-1 2;2 2;4 -2'
A = scipy.mat(s)
U, s, Vh=scipy.linalg.svd(A,True)
print U
print s
print Vh

U, s, Vh=scipy.linalg.svd(A,False)
print U
print s
print Vh