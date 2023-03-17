# Before going into C with the optimization rutine
# we test the projected coordinate gradient descent here
# to make sure it works or it makes sense to try this approach

import matplotlib.pyplot as plt
import numpy as np
from numpy.linalg import norm
from math import sqrt, pi
import intermediateTests as itt
from scipy.optimize import root_scalar # to project back blocks [mu_k, lambda_k+1]

def arclengthSimpson(mu, lam, xFrom, Bfrom, xTo, Bto):
     '''
     arclength along a boundary from xLam to xMu
     '''
     Bmu = itt.gradientBoundary(mu, xFrom, Bfrom, xTo, Bto)
     Blam = itt.gradientBoundary(lam, xFrom, Bfrom, xTo, Bto)
     B_mid = itt.gradientBoundary((mu + lam)/2, xFrom, Bfrom, xTo, Bto)
     return (norm(Bmu) + 4*norm(B_mid) + norm(Blam))*(abs(mu - lam)/6)

def hermite_interpolationT(param, x0, T0, grad0, x1, T1, grad1):
    '''
    Hermite interpolation of the eikonal
    '''
    sumGrads = (param**3 - 2*param**2 + param)*grad0 + (param**3 - param**2)*grad1
    return (2*param**3 - 3*param**2 + 1)*T0 + (-2*param**3 + 3*param**2)*T1 + np.dot(x1 - x0, sumGrads)

def der_hermite_interpolationT(param, x0, T0, grad0, x1, T1, grad1):
    '''
    derivative with respecto to param of the Hermite interpolation of the eikonal
    '''
    sumGrads = (3*param**2 - 4*param + 1)*grad0 + (3*param**2 - 2*param)*grad1
    return (6*param**2 - 6*param)*T0 + (-6*param**2 + 6*param)*T1 + np.dot(x1 - x0, sumGrads)

def t1(lam, x0, xk1, B0k1, Bk1, zk, Bk_mu):
    '''
    This function is useful to solve for lamMin
    '''
    yk1 = itt.hermite_boundary(lam, x0, B0k1, xk1, Bk1)
    return Bk_mu[0]*(yk1[1] - zk[1]) - Bk_mu[1]*(yk1[0] - zk[0])

def t2(lam, x0, xk1, B0k1, Bk1, zk):
    '''
    This function is useful to solve for lamMax
    '''
    yk1 = itt.hermite_boundary(lam, x0, B0k1, xk1, Bk1)
    Bk_lam = itt.gradientBoundary(lam , x0, B0k1, xk1, Bk1)
    return Bk_lam[0]*(yk1[1] - zk[1]) - Bk_lam[1]*(yk1[0] - zk[0])

# Find a root finding method

def fObj_noTops(params, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk):
    '''
    Objective function of an update without the tops on a triangle fan
    params = [mu1, lam2, mu2, lam3, mu3, ..., lambda_n, mu_n, lambda_n1] # length 2n
    listIndices = [eta1, eta2, ..., eta_n, eta_n1]       # length n+1
    listxk = [x0, x1, x2, ..., xn, xn1]                  # length n+2
    listB0k = [B01, B02, B03, ..., B0n, B0n1]            # length n+1
    listBk = [B1, B2, B3, ..., Bn, Bn1]                  # length n+1
    '''
    n = len(listxk) - 2
    muk = params[0]
    etak = listIndices[0]
    Bk = listBk[0]
    B0k = listB0k[0]
    zk = itt.hermite_boundary(muk, x0, B0k, x1, Bk)
    sum = hermite_interpolationT(muk, x0, T0, grad0, x1, T1, grad1)
    for i in range(1, n):
        k = 2*i -1 # starts in k = 1, all the way to k = 2n-3
        mukPrev = muk
        muk = params[k+1] # starts in mu2 ends in mu_n
        lamk = params[k] # starts in lam2 ends in lamn
        etaPrev = etak
        etak = listIndices[i]
        etaMin = min(etaPrev, etak)
        Bk = listBk[i]
        B0k = listB0k[i]
        xk = listxk[i+1]
        zkPrev = zk
        zk = itt.hermite_boundary(muk, x0, B0k, xk, Bk)
        yk = itt.hermite_boundary(lamk, x0, B0k, xk, Bk)
        sum += etaPrev*norm(yk - zkPrev) + etaMin*arclengthSimpson(muk, lamk, x0, B0k, xk, Bk)
    # now we need to add the last segment
    mukPrev = muk
    lamk = params[2*n-1] # last one
    etaPrev = etak
    etak = listIndices[n]
    etaMin = min(etak, etaPrev)
    Bk = listBk[n]
    B0k = listB0k[n]
    xk = listxk[n+1]
    zkPrev = zk
    yk = itt.hermite_boundary(lamk, x0, B0k, xk, Bk)
    sum += etaPrev*norm(yk - zkPrev) + etaMin*arclengthSimpson(lamk, 1, x0, B0k, xk, Bk)
    return sum

##########
## THESE ARE THE AUXILIARY FUNCTIONS FOR THE BLOCK COORDINATE PROJECTED GRADIENT DESCENT

def partial_fObj_mu1(mu1, x0, T0, grad0, x1, T1, grad1, gradB1_mu, y2, z1):
    der_hermite_inter = der_hermite_interpolationT(mu1, x0, T0, grad0, x1, T1, grad1)
    return der_hermite_inter - np.dot(gradB1_mu, y2 - z1)/norm(y2 - z1)

def partial_fObj_mu(muk, etakM1, gradBk_muk, yk, zkM1, etaMin):
    return etakM1*np.dot(-gradBk_muk, yk - zkM1)/norm(yk - zkM1) + etaMin*norm(gradBk_muk)

def partial_fObj_lambda(lambdak, etakM1, gradBk_lamk, yk, zkM1, etaMin):
    return etakM1*np.dot(gradBk_lamk, yk - zkM1)/norm(yk - zkM1) - etaMin*norm(gradBk_lamk)

def feasible_block(muk, lamk1, Bk_muk, Bk1_lamk1, yk1, zk):
    '''
    boolean function, returns true if the block [mu_k, lambda_k+1] is feasible
    returns false if not feasible
    '''
    ans = True
    if( muk > 1 or muk < 0):
        ans = False
    if( lamk1 > 1 or lamk1 < 0):
        ans = False
    Nk_muk = np.array([-Bk_muk[1], Bk_muk[0]])
    Nk1_lamk1 = np.array([-Bk1_lamk1[1], Bk1_lamk1[0]])
    if( np.dot(Nk_muk1, yk1 - zk) > 0 or np.dot(Nk1_lamk1, yk1 - zk) > 0):
        ans = False
    return ans

def project_block(muk, lamk1, Bk_muk, Bk1_lamk1, yk1, zk, x0, xk1, B0k1, Bk1):
    '''
    Project a block [mu_k, lambda_k+1] such that it is feasible
    '''
    Nk_muk = np.array([-Bk_muk[1], Bk_muk[0]])
    Nk1_lamk1 = np.array([-Bk1_lamk1[1], Bk1_lamk1[0]])
    dotTestMin = np.dot( yk1 - zk, Nk_muk )
    dotTestMax = np.dot( yk1 - zk, Nk1_lamk1 )
    # Test if lamk < lamMin
    if( dotTestMin < 0):
        # Means that we need to find lambdaMin
        tMin = lambda lam: t1(lam, x0, xk1, B0k1, Bk1, zk, Bk_muk)
        # Find the root of tMin
        rootMin = root_scalar(tMin, bracket=[0, 1])
        lamk1 = rootMin.root
    if( dotTestMax < 0):
        # Means that we need to find lambdaMax
        tMax = lambda lam: t2(lam, x0, xk1, B0k1, Bk1, zk)
        rootMax = root_scalar(tMax, bracket=[0, 1])
        lamk1 = rootMax.root
    if( muk < 0):
        muk = 0
    elif( muk > 1):
        muk = 1
    if( lamk1 < 0):
        lamk1 = 0
    elif( lamk1 > 1):
        lamk1 = 1
    return muk, lamk1
    
## TESTS FOR THESE FUNCTIONS

x0 = np.array([0.0,0.0])
x1 = np.array([2, -0.2])
x2 = np.array([1.5, 0.8])
x3 = np.array([0.2, 1.2])
xHat = np.array([-0.8, 0.7])
B01 = np.array([2.2, 1])
B01 = B01/norm(B01)
B02 = np.array([1, 1.5])
B02 = B02/norm(B02)
B03 = np.array([0.2, 2])
B03 = B03/norm(B03)
B0Hat = np.array([-1, 0.4])
B0Hat = B0Hat/norm(B0Hat)
B1 = np.array([1, -0.6])
B1 = B1/norm(B1)
B2 = np.array([2, -0.2])
B2 = B2/norm(B2)
B3 = np.array([1, 2])
B3 = B3/norm(B3)
BHat = np.array([-1, 1])
BHat = BHat/norm(BHat)

# params = [mu1, lam2, mu2, lam3, mu3, lam4, mu4, ..., lambda_n, mu_n, lambda_n1]
mu1 = 0.15
lam2 = 0.15
mu2 = 0.13
lam3 = 0.17
mu3 = 0.15
lam4 = 1
params = [mu1, lam2, mu2, lam3, mu3, lam4]

xSource = np.array([ 1, -0.5 ])
T0 = norm(xSource - x0)
grad0 = (x0 - xSource)/T0
T1 = norm(xSource - x1)
grad1 = (x1 - xSource)/T1

THat_true = norm(xHat - xSource)

listIndices = [1.0, 1.0, 1.0, 1.0]
listxk = [x0, x1, x2, x3, xHat]
listB0k = [B01, B02, B03, B0Hat]
listBk = [B1, B2, B3, BHat]


# Starting to plot everything

itt.plotFan3(x0, B01, B02, B03, B0Hat, x1, B1, x2, B2, x3, B3, xHat, BHat, mu1 = mu1, lam2 = lam2, mu2 = mu2, lam3 = lam3, mu3 = mu3, lam4 = lam4)

plt.scatter(xSource[0], xSource[1], s = 20, c = "#ff00f2")
plt.plot([xSource[0], xHat[0]], [xSource[1], xHat[1]], linestyle = ':', c = "#ab00a3")


f_init = fObj_noTops(params, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)

