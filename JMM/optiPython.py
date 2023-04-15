


# Before going into C with the optimization rutine
# we test the projected coordinate gradient descent here
# to make sure it works or it makes sense to try this approach

import matplotlib.pyplot as plt
import numpy as np
from numpy.linalg import norm
from math import sqrt, pi
import intermediateTests as itt
from scipy.optimize import root_scalar # to project back blocks [mu_k, lambda_k+1]
import colorcet as cc
import matplotlib.colors as clr


# colormap2  = clr.LinearSegmentedColormap.from_list('Retro',
#                                                    [(0,    '#000000'),
#                                                     (0.1, '#2c3454'),
#                                                     (0.25, '#0033ff'),
#                                                     (0.60, '#00f3ff'),
#                                                     (1,    '#e800ff')], N=256)

colormap2 = "cet_linear_worb_100_25_c53_r"
colormap2_r = "cet_linear_worb_100_25_c53"

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


####### Projections

## Finding lamk1Min and lamk1Max given muk

def t1(lam, x0, xk1, B0k1, Bk1, zk, Bk_mu):
    '''
    This function is useful to solve for lamk1Min
    given muk
    '''
    yk1 = itt.hermite_boundary(lam, x0, B0k1, xk1, Bk1)
    return Bk_mu[0]*(yk1[1] - zk[1]) - Bk_mu[1]*(yk1[0] - zk[0])

def t2(lam, x0, xk1, B0k1, Bk1, zk):
    '''
    This function is useful to solve for lamk1Max
    given muk
    '''
    yk1 = itt.hermite_boundary(lam, x0, B0k1, xk1, Bk1)
    Bk_lam = itt.gradientBoundary(lam , x0, B0k1, xk1, Bk1)
    return Bk_lam[0]*(yk1[1] - zk[1]) - Bk_lam[1]*(yk1[0] - zk[0])

## Find mukMin and mukMAx given lamk1

def t3(mu, x0, xk, B0k, Bk, yk1):
     '''
     This function is useful to solve for mukMax
     given lamk1
     '''
     zk = itt.hermite_boundary(mu, x0, B0k, xk, Bk)
     Bk_mu = itt.gradientBoundary(mu, x0, B0k, xk, Bk)
     return Bk_mu[0]*(yk1[1] - zk[1]) - Bk_mu[1]*(yk1[0] - zk[0])
     

def t4(mu, x0, xk, B0k, Bk, yk1, Bk_lam):
     '''
     This function is useful to solve for mukMin
     given lamk1
     '''
     zk = itt.hermite_boundary(mu, x0, B0k, xk, Bk)
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



          

def partial_L_muk(muk, lamk, B0k_muk, secondDer_B0k_muk, B0k_halves, secondDer_B0khalves_muk, B0k_lamk):
     '''
     partial of the approximation of the arc length with respect to muk
     '''
     if( abs(muk - lamk) <= 1e-14):
          return 0
     else:
          normB0k_muk = norm(B0k_muk)
          normB0k_halves = norm(B0k_halves)
          sk = get_sk(muk, lamk)
          firstPart = sk/6*(normB0k_muk + 4*normB0k_halves + norm(B0k_lamk) )
          secondPart = (abs(muk - lamk)/6)*(np.dot(secondDer_B0k_muk, B0k_muk)/normB0k_muk + 2*np.dot(secondDer_B0khalves_muk, B0k_halves)/normB0k_halves)
          return firstPart + secondPart

def partial_L_lamk(muk, lamk, B0k_muk, B0k_halves, secondDer_B0khalves_lamk, B0k_lamk, secondDer_B0k_lamk):
     '''
     partial of the approximation of the arc length with respect to lamk
     '''
     if( abs(muk - lamk) <= 1e-14):
          return 0
     else:
          normB0k_halves = norm(B0k_halves)
          normB0k_lamk = norm(B0k_lamk)
          sk = get_sk(muk, lamk)
          firstPart = -sk/6*(norm(B0k_muk) + 4*normB0k_halves + normB0k_lamk )
          secondPart = (abs(muk - lamk)/6)*(2*np.dot(secondDer_B0khalves_lamk, B0k_halves)/normB0k_halves + np.dot(secondDer_B0k_lamk, B0k_lamk)/normB0k_lamk )
     return firstPart + secondPart
     

def partial_fObj_mu1(mu1, x0, T0, grad0, x1, T1, grad1, B01_mu, y2, z1):
     der_hermite_inter = der_hermite_interpolationT(mu1, x0, T0, grad0, x1, T1, grad1)
     if( norm(y2 - z1) < 1e-8 ):
          return der_hermite_inter
     else:
          return der_hermite_inter - np.dot(B01_mu, y2 - z1)/norm(y2 - z1)


def partial_fObj_recCr(shFrom, shTo, rec, x0, B0kM1, xkM1, BkM1, B0k, xk, Bk, etakM1, etak):
     '''
     Partial of the objective function  with respect to a receiver that creeps to a shooter
     (originally the reciver is lamk, the shooter where it comes from is mukM1 and the
     shooter to where it creeps is muk)
     '''
     zkM1 = itt.hermite_boundary(shFrom, x0, B0kM1, xkM1, BkM1)
     yk = itt.hermite_boundary(rec, x0, B0k, xk, Bk)
     B0k_shTo = itt.gradientBoundary(shTo, x0, B0k, xk, Bk)
     secondDer_B0k_rec = itt.secondDer_Boundary(rec, x0, B0k, xk, Bk)
     B0k_halves = itt.gradientBoundary( (shTo + rec)/2, x0, B0k, xk, Bk)
     secondDer_B0khalves_rec = itt.secondDer_Boundary((shTo + rec)/2, x0, B0k, xk, Bk)
     B0k_rec = itt.gradientBoundary(rec, x0, B0k, xk, Bk)
     perL_rec = partial_L_lamk(shTo, rec, B0k_shTo, B0k_halves, secondDer_B0khalves_rec, B0k_rec, secondDer_B0k_rec)
     etaMin = min(etakM1, etak)
     if( shFrom == rec ):
          return etaMin*perL_rec
     else:
          return etakM1*np.dot(B0k_rec, yk - zkM1)/norm(yk - zkM1) + etaMin*perL_rec

def partial_fObj_shCr(sh, recFrom, recTo, x0, B0k, xk, Bk, B0k1, xk1, Bk1, etak, etakM1):
     '''
     Partial of the objective function with respect to a shooter that creeps from a receiver
     '''
     zk = itt.hermite_boundary(sh, x0, B0k, xk, Bk)
     yk1 = itt.hermite_boundary(recTo, x0, B0k1, xk1, Bk1)
     B0k_sh = itt.gradientBoundary(sh, x0, B0k, xk, Bk)
     secondDer_B0k_sh = itt.secondDer_Boundary(sh, x0, B0k, xk, Bk)
     B0k_halves = itt.gradientBoundary((sh + recFrom)/2, x0, B0k, xk, Bk)
     secondDer_B0khalves_sh = itt.secondDer_Boundary((sh + recFrom)/2, x0, B0k, xk, Bk)
     B0k_recFrom = itt.gradientBoundary(recFrom, x0, B0k, xk, Bk)
     parL_sh = partial_L_muk(sh, recFrom, B0k_sh, secondDer_B0k_sh, B0k_halves, secondDer_B0khalves_sh, B0k_recFrom)
     etaMin = min(etak, etakM1)
     if( sh == recTo ):
          return etaMin*parL_sh
     else:
          return etakM1*np.dot(-B0k_sh, yk1 - zk)/norm(yk1 - zk) + etaMin*parL_sh


def partial_fObj_recCr1(muk, muk1, lamk1, x0, B0k, xk, Bk, B0k1, xk1, Bk1, etak, etak1):
     '''
     Partial of the objective function of the "next" receiver that creeps to a shooter
     '''
     zk = itt.hermite_boundary(muk, x0, B0k, xk, Bk)
     yk1 = itt.hermite_boundary(lamk1, x0, B0k1, xk1, Bk1)
     B0k1_muk1 = itt.gradientBoundary(muk1, x0, B0k1, xk1, Bk1)
     secondDer_B0k1_lamk1 = itt.secondDer_Boundary(lamk1, x0, B0k1, xk1, Bk1)
     B0k1_halves = itt.gradientBoundary( (muk1 + lamk1)/2, x0, B0k1, xk1, Bk1)
     secondDer_B0k1halves_lamk1 = itt.secondDer_Boundary((muk1 + lamk1)/2, x0, B0k1, xk1, Bk1)
     B0k1_lamk1 = itt.gradientBoundary(lamk1, x0, B0k1, xk1, Bk1)
     perL_lamk1 = partial_L_lamk(muk1, lamk1, B0k1_muk1, B0k1_halves, secondDer_B0k1halves_lamk1, B0k1_lamk1, secondDer_B0k1_lamk1)
     etaMin = min(etak, etak1)
     if( muk == lamk1 ):
          return etaMin*perL_lamk1
     else:
          return etak*np.dot(B0k1_lamk1, yk1 - zk)/norm(yk1 - zk) + etaMin*perL_lamk1



def project_lamk1Givenmuk(muk, lamk1, x0, B0k, xk, Bk, B0k1, xk1, Bk1):
    '''
    Project back lamk1 given muk
    '''
    lamk1 = project_box(lamk1)
    zk = itt.hermite_boundary(muk, x0, B0k, xk, Bk)
    yk1 = itt.hermite_boundary(lamk1, x0, B0k1, xk1, Bk1)
    B0k_muk = itt.gradientBoundary(muk, x0, B0k, xk, Bk)
    B0k1_lamk1 = itt.gradientBoundary(lamk1, x0, B0k1, xk1, Bk1)
    
    Nk_muk = np.array([-B0k_muk[1], B0k_muk[0]])
    Nk1_lamk1 = np.array([-B0k1_lamk1[1], B0k1_lamk1[0]])
    dotTestMin = np.dot( yk1 - zk, Nk_muk )
    dotTestMax = np.dot( yk1 - zk, Nk1_lamk1 )
    #print("       dotTestMin: ", dotTestMin, "  dotTestMax: ", dotTestMax)
    # Test if lamk < lamMin
    if( dotTestMin < 0):
        # print("  failed dotTestMin project lamk1 given muk")
        # print("  zk: ", zk, "  yk1: ", yk1)
        # print("  muk: ", muk, " lamk1: ", lamk1)
        # print("  B0k: ", B0k, "  xk: ", xk, "  Bk: ", Bk)
        # print("  B0k1: ", B0k1, "  xk1: ", xk1, "  Bk1: ", Bk1)
        # Means that we need to find lambdaMin
        tMin = lambda lam: t1(lam, x0, xk1, B0k1, Bk1, zk, B0k_muk)
        # Find the root of tMin
        rootMin = root_scalar(tMin, bracket=[0, 1])
        lamk1 = rootMin.root
        yk1 = itt.hermite_boundary(lamk1, x0, B0k1, xk1, Bk1)
        B0k1_lamk1 = itt.gradientBoundary(lamk1, x0, B0k1, xk1, Bk1)
        Nk1_lamk1 = np.array([-B0k1_lamk1[1], B0k1_lamk1[0]])
        dotTestMax = np.dot( yk1 - zk, Nk1_lamk1 )
        #print("       lambda < lambdaMin")
    if( dotTestMax < 0):
        # print("  failed dotTestMax project lamk1 given muk")
        # print("  zk: ", zk, "  yk1: ", yk1)
        # print("  muk: ", muk, " lamk1: ", lamk1)
        # print("  B0k: ", B0k, "  xk: ", xk, "  Bk: ", Bk)
        # print("  B0k1: ", B0k1, "  xk1: ", xk1, "  Bk1: ", Bk1)
        # Means that we need to find lambdaMax
        tMax = lambda lam: t2(lam, x0, xk1, B0k1, Bk1, zk)
        rootMax = root_scalar(tMax, bracket=[0, 1])
        lamk1 = rootMax.root
        #print("       lambda > lambdaMax")
    lamk1 = project_box(lamk1) # Such that 0<=lamk1 <=1
    return lamk1

def project_mukGivenlamk1(muk, lamk1, x0, B0k, xk, Bk, B0k1, xk1, Bk1):
     '''
     Project back muk given lamk1
     '''
     muk = project_box(muk)
     yk1 = itt.hermite_boundary(lamk1, x0, B0k1, xk1, Bk1)
     B0k1_lamk1 = itt.gradientBoundary(lamk1, x0, B0k1, xk1, Bk1)
     zk = itt.hermite_boundary(muk, x0, B0k, xk, Bk)
     B0k_muk = itt.gradientBoundary(muk, x0, B0k, xk, Bk)
     # Compute the normals
     N0k1_lamk1 = np.array([-B0k1_lamk1[1], B0k1_lamk1[0]])
     N0k_muk = np.array([-B0k_muk[1], B0k_muk[0]])
     dotTestMin =  np.dot(N0k1_lamk1, yk1 - zk)
     dotTestMax = np.dot(N0k_muk, yk1 - zk)
     if(dotTestMin<0 ):
          # print("  failed dotTestMin project muk given lamk1")
          # print("  zk: ", zk, "  yk1: ", yk1)
          # print("  muk: ", muk, " lamk1: ", lamk1)
          # print("  B0k: ", B0k, "  xk: ", xk, "  Bk: ", Bk)
          # print("  B0k1: ", B0k1, "  xk1: ", xk1, "  Bk1: ", Bk1)
          tMin = lambda mu: t4(mu, x0, xk, B0k, Bk, yk1, B0k1_lamk1)
          rootMin = root_scalar(tMin, bracket = [0,1])
          muk = rootMin.root
          zk = itt.hermite_boundary(muk, x0, B0k, xk, Bk)
          B0k_muk = itt.gradientBoundary(muk, x0, B0k, xk, Bk)
          N0k_muk = np.array([-B0k_muk[1], B0k_muk[0]])
          dotTestMax = np.dot(N0k_muk, yk1 - zk)
     if(dotTestMax<0 ):
          # print("  failed dotTestMax project muk given lamk1")
          # print("  zk: ", zk, "  yk1: ", yk1)
          # print("  muk: ", muk, " lamk1: ", lamk1)
          # print("  B0k: ", B0k, "  xk: ", xk, "  Bk: ", Bk)
          # print("  B0k1: ", B0k1, "  xk1: ", xk1, "  Bk1: ", Bk1)
          tMax = lambda mu: t3(mu, x0, xk, B0k, Bk, yk1)
          rootMax = root_scalar(tMax, bracket = [0, 1])
          muk = rootMax.root
     muk = project_box(muk)
     return muk

     
def project_ontoLine(d):
     '''
     Projection of a vector d along the line x=y
     '''
     projector = 0.5*np.array([ [1,1], [1,1]])
     return projector@d

def close_to_identity(lamk, muk):
     '''
     Computes the distance of the vector [lamk, muk]
     to the line lamk = muk
     '''
     p = np.array([lamk, muk])
     proj = project_ontoLine(p)
     return norm(p - proj)



def backTrClose_block(alpha0, k, dlamk, dmuk, params, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk):
     '''
     Backtracking to find the next block [lamk, muk]
     it considers two directions: steepest descent
                                  steepest descent projected onto the line lamk = muk
     '''
     f_before = fObj_noTops(params, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
     i = 0
     d_middle = np.array([dlamk, dmuk]) # "normal" steespest descent
     params_test = np.copy(params)
     alpha = alpha0*0.2*1/(max(norm(d_middle), 1))
     params_test[k:(k+2)] = params[k:(k+2)] - alpha*d_middle
     params_test_proj = np.copy(params)
     params_test_proj[k:(k+2)] = project_ontoLine(params_test[k:(k+2)])
     # Compare the function value
     f_test = fObj_noTops(params_test, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
     f_test_proj = fObj_noTops(params_test_proj, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
     while( (f_test < f_before or f_test_proj < f_before) and i < 8):
          alpha = alpha*1.3 # Increase step size
          params_test[k:(k+2)] = params[k:(k+2)] - alpha*d_middle
          params_test_proj[k:(k+2)] = project_ontoLine(params_test[k:(k+2)])
          f_test = fObj_noTops(params_test, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
          f_test_proj = fObj_noTops(params_test_proj, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
          i += 1
     i = 0
     while( f_before <= f_test and f_before <= f_test_proj and i < 25 ):
          alpha = alpha*0.2
          params_test[k:(k+2)] = params[k:(k+2)] - alpha*d_middle
          params_test_proj[k:(k+2)] = project_ontoLine(params_test[k:(k+2)])
          f_test = fObj_noTops(params_test, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
          f_test_proj = fObj_noTops(params_test_proj, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
          i += 1
     if( f_before <= f_test and f_before <= f_test_proj ):
          return params[k], params[k+1]
     elif( f_test < f_test_proj):
          return params_test[k], params_test[k+1]
     elif( f_test_proj <= f_test ):
          return params_test_proj[k], params_test_proj[k+1]

def backTr_block(alpha0, k, dlamk, dmuk, params, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk):
     '''
     Backtracking to find the next block [lamk, muk]
     it considers one direction:  steepest descent
     '''
     f_before = fObj_noTops(params, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
     i = 0
     d_middle = np.array([dlamk, dmuk]) # "normal" steespest descent
     params_test = np.copy(params)
     alpha = alpha0*0.2*1/(max(norm(d_middle), 1))
     params_test[k:(k+2)] = params[k:(k+2)] - alpha*d_middle
     # Compare the function value
     f_test = fObj_noTops(params_test, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
     while( f_test < f_before and i < 8):
          alpha = alpha*1.3 # Increase step size
          params_test[k:(k+2)] = params[k:(k+2)] - alpha*d_middle
          f_test = fObj_noTops(params_test, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
          i += 1
     i = 0
     while( f_before <= f_test  and i < 25):
          alpha = alpha*0.2
          params_test[k:(k+2)] = params[k:(k+2)] - alpha*d_middle
          f_test = fObj_noTops(params_test, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
          i += 1
     if( f_before <= f_test ):
          return params[k], params[k+1]
     else:
          return params_test[k], params_test[k+1]


def forwardPassUpdate(params0, gammas, theta_gamma, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk):
     '''
     gammas : radius for the circle centered at [lamk, muk], if such circle intersects the line lamk = muk then do a close update, it is an array of size nRegions - 1 (notice that it can be an array of size 0)
     theta_gamma : rate of decrease in the circle centered at [lamk, muk]
     Updates blocks     [mu1]
                        [lam2, mu2]
                        [lamk, muk]
                        [lamn1]
     '''
     # First parameter to update: mu1
     params = np.copy(params0)
     mu1 = params[0]
     lam2 = params[1]
     B0k = listB0k[0]
     xk = listxk[1]
     Bk = listBk[0]
     B0k1 = listB0k[1]
     xk1 = listxk[2]
     Bk1 = listBk[1]
     B0k_muk = itt.gradientBoundary(mu1, x0, B0k, xk, Bk)
     yk1 = itt.hermite_boundary(lam2, x0, B0k1, xk1, Bk1)
     zk = itt.hermite_boundary(mu1, x0, B0k, xk, Bk)
     # Compute direction for muk
     dmuk = partial_fObj_mu1(mu1, x0, T0, grad0, x1, T1, grad1, B0k_muk, yk1, zk)
     alpha = backTr_coord(2, 0, dmuk, params, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
     mu1 = mu1 - alpha*dmuk
     mu1 = project_mukGivenlamk1(mu1, lam2, x0, B0k, xk, Bk, B0k1, xk1, Bk1) # project back so that it is feasible
     params[0] = mu1
     # Now we start with the blocks of size 2
     nRegions = len(listxk) - 2
     for j in range(1, nRegions):
          k = 2*j # From 2 to 2nRegions - 2
          gamma = gammas[j - 1]
          mukM1 = params[k-2]
          lamk = params[k-1]
          muk = params[k]
          lamk1 = params[k+1]
          B0kM1 = listB0k[j-1]
          xkM1 = listxk[j]
          BkM1 = listBk[j-1]
          B0k = listB0k[j]
          xk = listxk[j+1]
          Bk = listBk[j]
          B0k1 = listB0k[j+1]
          xk1 = listxk[j+2]
          Bk1 = listBk[j+1]
          etakM1 = listIndices[j-1]
          etak = listIndices[j]
          etak1 = listIndices[j+1]
          # Compute directions
          dlamk = partial_fObj_recCr(mukM1, muk, lamk, x0, B0kM1, xkM1, BkM1, B0k, xk, Bk, etakM1, etak)
          dmuk = partial_fObj_shCr(muk, lamk, lamk1, x0, B0k, xk, Bk, B0k1, xk1, Bk1, etak, etakM1)
          # See if we need to do a close update or not
          r = close_to_identity(lamk, muk)
          if( r <= gamma ):
               # Meaning we have to do a close update
               lamk, muk = backTrClose_block(2, k-1, dlamk, dmuk, params, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
               gamma = gamma*theta_gamma
               gammas[j - 1] = gamma # Update this gamma
          else:
               # We don't have to consider a close update
               lamk, muk = backTr_block(2, k-1, dlamk, dmuk, params, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
          # Either way we need to project back to the feasible set
          lamk = project_lamk1Givenmuk(mukM1, lamk, x0, B0kM1, xkM1, BkM1, B0k, xk, Bk)
          muk = project_mukGivenlamk1(muk, lamk1, x0, B0k, xk, Bk, B0k1, xk1, Bk1)
          # Update
          params[k-1] = lamk
          params[k] = muk
     # Finally update lamn1
     mun = params[2*nRegions - 2]
     lamn1 = params[2*nRegions - 1]
     mun1 = 1 # Always
     B0kM1 = listB0k[nRegions - 1]
     xkM1 = listxk[nRegions ]
     BkM1 = listBk[nRegions - 1]
     B0k = listB0k[nRegions ]
     xk = listxk[nRegions + 1]
     Bk = listBk[nRegions ]
     etakM1 = listIndices[nRegions - 2]
     etak = listIndices[nRegions - 1]
     # Compute direction
     dlamn1 = partial_fObj_recCr(mun, mun1, lamn1, x0, B0kM1, xkM1, BkM1, B0k, xk, Bk, etakM1, etak)
     # Compute step size
     alpha = backTr_coord(2, (2*nRegions - 1), dlamn1, params, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
     # Update
     lamn1 = lamn1 - alpha*dlamn1
     # Project back
     lamn1 = project_lamk1Givenmuk(mun, lamn1, x0, B0kM1, xkM1, BkM1, B0k, xk, Bk)
     # Update
     params[2*nRegions - 1] = lamn1
     return params, gammas
     



def project_box(param):
     if(param < 0):
          param = 0
     elif(param > 1):
          param = 1
     else:
          param = param
     return param

def backTr_coord(alpha0, k, d, params, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk):
     '''
     Coordinate backtracking to find the step size for coordinate gradient descent
     '''
     i = 0
     alpha = alpha0*0.2/(max(abs(d), 1))
     f_before = fObj_noTops(params, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
     params_test = np.copy(params)
     params_test[k] = params[k] - alpha*d
     f_after = fObj_noTops(params_test, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
     while( f_after < f_before and i < 8 ):
          alpha = alpha*1.3 # increase step size
          params_test[k] = params[k] - alpha*d
          f_after = fObj_noTops(params_test, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
          i += 1
     i = 0
     while( f_before <= f_after and i < 25):
          alpha = alpha*0.2
          params_test[k] = params[k] - alpha*d
          f_after = fObj_noTops(params_test, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
          i += 1
     if( f_before <= f_after):
          alpha = 0
     return alpha


def get_sk(muk, lamk):
     if(muk > lamk):
          sk = 1
     else:
          sk = -1
     return sk


def gradient_TY(params, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk):
     '''
     Gradient of the objective function TY
     '''
     n = len(listxk) - 2
     gradient = np.zeros((2*n + 1))
     muk = params[0]
     lamk1 = params[1]
     muk1 = params[2]
     B01_mu = itt.gradientBoundary(muk, x0, listB0k[0], listxk[1], listBk[0])
     yk1 = itt.hermite_boundary(lamk1, x0, listB0k[1], listxk[2], listBk[1])
     zk = itt.hermite_boundary(muk, x0, listB0k[0], listxk[1], listBk[0])
     gradient[0] = partial_fObj_mu1(params[0], x0, T0, grad0, x1, T1, grad1, B01_mu, yk1, zk)
     gradient[1] = partial_fObj_recCr1(muk, muk1, lamk1, x0, listB0k[0], listxk[1], listBk[0], listB0k[1], listxk[2], listBk[1], listIndices[1], listIndices[0])
     for j in range(1,n):
          k = 2*j
          etakM1 = listIndices[j-1]
          etak = listIndices[j]
          etak1 = listIndices[j+1]
          lamk = params[k-1]
          muk = params[k]
          lamk1 = params[k+1]
          muk1 = params[k+2]
          gradient[k] = partial_fObj_shCr(muk, lamk, lamk1, x0, listB0k[j], listxk[j+1], listBk[j], listB0k[j+1], listxk[j+2], listBk[j+1], etak, etakM1)
          gradient[k+1] = partial_fObj_recCr1(muk, muk1, lamk1, x0, listB0k[j], listxk[j+1], listBk[j], listB0k[j+1], listxk[j+2], listBk[j+1], etak1, etak)
     gradient[2*n] = 0
     return gradient



def blockCoordinateGradient(params0, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk, maxIter, tol, theta_gamma = 1, plotSteps = True, saveIterates = False):
     '''
     Block coordinate subgradient descent (modified) for an update in a triangle fan without
     tops. Inspired by gradient sampling but in this case we know where our (geometric)
     singularities are and thus we don't need to calculate explicitly the convex hull
     '''
     params = np.copy(params0)
     params = np.append(params, [1])
     #print(" Initial params: \n", params)
     # Initialize the useful things
     listObjVals = []
     listGrads = []
     listChangefObj = []
     listIterates = []
     listGradIterations = []
     nRegions = len(listxk) -2
     gammas = 0.05*np.ones((nRegions - 1)) # Might be an array of length 0, it's fine
     gradk = gradient_TY(params, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
     norm_gradk = norm(gradk)
     fVal = fObj_noTops(params, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
     listGrads.append(norm_gradk)
     listObjVals.append(fVal)
     iter = 0
     change_fVal = 1
     while( abs(change_fVal) > tol and iter < maxIter):
          # Start with a forward pass
          params, gammas = forwardPassUpdate(params, gammas, theta_gamma, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
          gradk = gradient_TY(params, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
          norm_gradk = norm(gradk)
          fVal_prev = fVal
          fVal = fObj_noTops(params, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
          change_fVal = fVal_prev - fVal
          listGrads.append(norm_gradk)
          listObjVals.append(fVal)
          listChangefObj.append( change_fVal )
          iter += 1
          if plotSteps:
               itt.plotFann(x0, listB0k, listxk, listBk, params = params)
          if saveIterates:
               listIterates.append( params )
               listGradIterations.append( gradk)
     if saveIterates:
          return params, listObjVals, listGrads, listChangefObj, listIterates, listGradIterations
     else:
          return params, listObjVals, listGrads, listChangefObj
     


def plotResults(x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listB0k, listxk, listBk, params0, paramsOpt, listObjVals, listGrads, listChangefObj, trueSol = None, contours = True):
     '''
     Plots results from blockCoordinateGradient
     '''
     # First plot the original parameters
     itt.plotFann(x0, listB0k, listxk, listBk, params = params0)
     plt.title("Initial parameters")
     # Then plot the parameters found by this method
     itt.plotFann(x0, listB0k, listxk, listBk, params = paramsOpt)
     plt.title("Optimal parameters found")
     # Now plot the function value at each iteration
     fig = plt.figure(figsize=(800/96, 800/96), dpi=96) 
     plt.semilogy( range(0, len(listChangefObj)), listChangefObj, c = "#394664", linewidth = 0.8)
     plt.xlabel("Iteration")
     plt.ylabel("Change of function value")
     plt.title("Change of function value at each iteration")
     # Now plot the function value at each iteration
     fig = plt.figure(figsize=(800/96, 800/96), dpi=96)
     plt.semilogy( range(0, len(listObjVals)), listObjVals, c = "#396064", linewidth = 0.8)
     plt.xlabel("Iteration")
     plt.ylabel("Function value")
     plt.title("Function value at each iteration")
     # Now plot the norm of the gradient at each iteration
     fig = plt.figure(figsize=(800/96, 800/96), dpi=96) 
     plt.semilogy( range(0, len(listGrads)), listGrads, c = "#4d3964", linewidth = 0.8)
     plt.xlabel("Iteration")
     plt.ylabel("Norm of (sub)gradient")
     plt.title("Norm of (sub)gradient at each iteration")
     # For pairs of parameters we plot level sets
     nRegions = len(listxk) - 2
     fObjMesh = np.empty((200,200))
     for k in range(2*nRegions - 1):
          # We plot level sets by changins sequential parameters (2 at a time)
          param1, param2 = np.meshgrid( np.linspace(0,1,200), np.linspace(0,1,200) )
          # Compute the solution, compute this level set
          for i in range(200):
               for j in range(200):
                    p1 = param1[i,j]
                    p2 = param2[i,j]
                    paramsMesh = np.copy(paramsOpt)
                    paramsMesh[k] = p1
                    paramsMesh[k+1] = p2
                    fObjMesh[i,j] = fObj_noTops(paramsMesh, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk)
          # Plot it
          fig = plt.figure(figsize=(800/96, 800/96), dpi=96)
          im = plt.imshow(fObjMesh, cmap = colormap2, extent = [0,1,0,1], origin = "lower")
          plt.scatter(paramsOpt[k], paramsOpt[k+1], c = "white", marker = "*", label = "optimum found")
          if(contours):
               plt.contour(param1[0, :], param1[0, :], fObjMesh, cmap = colormap2_r, extent = [0,1,0,1], origin = "lower", levels = 15)
          plt.title("Level set of objective function")
          plt.xlabel("Parameter " + str(k))
          plt.ylabel("Parameter " + str(k+1))
          plt.legend()
          plt.colorbar(im)
     # If we know the true solution for this triangle fan, plot the decrease in the error
     if trueSol is not None:
          errRel = np.array(listObjVals)
          errRel = abs(errRel-trueSol)/trueSol
          fig = plt.figure(figsize=(800/96, 800/96), dpi=96)
          plt.semilogy( range(0, len(listObjVals)), errRel, c = "#00011f", linewidth = 0.8)
          plt.xlabel("Iteration")
          plt.ylabel("Relative error")
          plt.title("Relative error at each iteration")

######################################################
######################################################
######################################################
######################################################
######################################################
# Optimization for a generalized triangle fan i.e. the tops of the triangle fan are curved parametric curves

def fObj_generalized(params, x0, T0, grad0, x1, T1, grad1, xHat, listIndices, listxk, listB0k, listBk, listBkBk1,
                     indCrTop = None, paramsCrTop = None, indStTop = None, paramsStTop = None):
     '''
     Generalized objective function for when the tops on the triangle fan are also parametric curves.
     '''
     # Set indStTop if indCrTop is given
     if(paramsStTop is None):
          indStTop = [0]
          paramsStTop = [0,0]
     # Set indCrTop if indStTop is given
     if(paramsCrTop is None):
          indCrTop = [0]
          paramsCrTop = [0,0]
     currentCrTop = 0
     currentStTop = 0
     n = len(listxk) - 2
     muk = params[0]
     etak = listIndices[0]
     Bk = listBk[0]
     B0k = listB0k[0]
     zk = itt.hermite_boundary(muk, x0, B0k, x1, Bk)
     sum = hermite_interpolationT(muk, x0, T0, grad0, x1, T1, grad1)
     for j in range(1, n+1):
          # j goes from 1 to n
          # We have to circle around all the regions
          k = 2*j - 1  # Starts in k = 1, all the way to k = 2n - 1
          nTop = j # Number of boundary on the top that we are considering
          mukM1 = params[k-1]
          lamk = params[k]
          muk = params[k+1]
          B0k = listB0k[j]
          xkM1 = listxk[j]
          xk = listxk[j+1]
          Bk = listBk[j]
          BkBk1_0 = listBkBk1[k-1] # grad of hkhk1 at xk
          BkBk1_1 = listBkBk1[k] # grad of hkhk1 at xk1
          etakPrev = etak
          etak = listIndices[j]
          etaMin = min(etakPrev, etak)
          # Compute the points
          zkPrev = zk
          zk = itt.hermite_boundary(muk, x0, B0k, xk, Bk)
          yk = itt.hermite_boundary(lamk, x0, B0k, xk, Bk)
          # Then we need to know if we have points on the triangle top
          # See if there are points on the triangle top and if they are associated with a creeping ray
          if( nTop == indCrTop[currentCrTop] ):
               # This means that there is creeping along this triangle top
               # Hence from zkPrev the path goes to ak and creeps to bk
               # which then shoots to yk and then creeps to zk
               etaRegionOutside = listIndices[n + j]
               etaMinCr = min(etaRegionOutside, etakPrev)
               rk = paramsStTop[2*currentStTop]
               sk = paramsStTop[2*currentStTop + 1]
               ak = itt.hermite_boundary(rk, xkM1, BkBk1_0, xk, BkBk1_1)
               bk = itt.hermite_boundary(sk, xkM1, BkBk1_0, xk, BkBk1_1)
               sum += etakPrev*norm( ak - zkPrev ) # shoots from zkPrev to ak
               sum += etaMinCr*arclengthSimpson(rk, sk, xkM1, BkBk1_0, xk, BkBk1_1) # creeps from ak to bk
               sum += etakPrev*norm( yk - bk ) # shoots from bk to yk
               sum += etaMin*arclengthSimpson(muk, lamk, x0, B0k, xk, Bk) # creeps from yk to zk
               # Update the current index of the creeping updates
               if (currentCrTop  < len(indCrTop) - 1):
                    currentCrTop += 1
          elif( nTop == indStTop[currentStTop]):
               # This means that there is no creeping along this triangle top, it goes
               # straight through that ouside region
               # from zkPrev the path goes to ak, from ak it goes to bk, from bk to yk
               # from yk it creeps to zk
               etaRegionOutside = listIndices[n + j]
               rk = paramsStTop[2*currentStTop]
               sk = paramsStTop[2*currentStTop + 1]
               ak = itt.hermite_boundary(rk, xkM1, BkBk1_0, xk, BkBk1_1)
               bk = itt.hermite_boundary(sk, xkM1, BkBk1_0, xk, BkBk1_1)
               sum += etakPrev*norm( ak - zkPrev ) # shoots from zkPrev to ak
               sum += etaRegionOutside*norm( bk - ak )  # shoots from ak to bk
               sum += etakPrev*norm( yk - bk ) # shoots from bk to yk
               sum += etaMin*arclengthSimpson(muk, lamk, x0, B0k, xk, Bk) # creeps from yk to zk
               # Update the current index of the creeping updates
               if (currentCrTop  < len(indCrTop) - 1):
                    currentCrTop += 1
          else:
               # This means that there are no points along this triangle top, we proceed as "usual"
               sum += etakPrev*norm(yk - zkPrev) + etaMin*arclengthSimpson(muk, lamk, x0, B0k, xk, Bk)
     return sum
          

################################
#### Knowing when an update is feasible


# Project back lamk given mukM1 when there is no creeping or shooting through the side edge

def project_lamkGivenmuk1_noCr(mukM1, lamk, x0, B0kM1, xkM1, BkM1, B0k, xk, Bk, BkM1Bk_0, BkM1Bk_1):
     '''
     Project back lamk given mukM1 when there is no creeping or shooting though the side edge xkxk1
     In this case we assume that the edge xkxk1 curves towards the inside of the curvy triangle
     we also assume that lamk in the previous iteration, lamkPrev is such that lamk > lamkPrev
     (otherwise we don't need to project back like this, we would just need a box projection)
     '''
     lamk = project_box(lamk) # Very first step in every projection method in here
     zkM1 = itt.hermite_boundary(mukM1, x0, B0kM1, xkM1, BkM1)
     yk = itt.hermite_boundary(lamk, x0, B0k, xk, Bk)
     B0kM1_mukM1 = itt.gradientBoundary(mukM1, x0, B0kM1, xkM1, BkM1)
     B0k_lamk = itt.gradientBoundary(lamk, x0, B0k, xk, Bk)
     # We need to find a_tan = hkM1hk(r_tan)
     rPass = lambda r: t2(r, xkM1, BkM1Bk_0, xk, BkM1Bk_1)
     rootTan = root_scalar(rPass, bracket = [0,1])
     r_tan = rootTan.root
     a_tan = itt.hermite_boundary(r_tan, xkM1, BkM1Bk_0, xk, BkM1Bk_1)
     BkM1Bk_tan = itt.gradientBoundary(r_tan, xkM1, BkM1Bk_0, xk, BkM1Bk_1)

     # The normals
     NkM1_mukM1 = np.array([-B0kM1_mukM1[1], B0kM1_mukM1[0]])
     Nk_lamk = np.array([-B0k_lamk[1], B0k_lamk[0]])
     N_tan = np.array([-BkM1Bk_tan[1], BkM1Bk_tan[0]])

     # Tests
     dotTestMin_fromh0kM1 = np.dot( yk - zkM1, NkM1_mukM1 ) # should be positive
     dotTestMax_fromh0kM1 = np.dot( yk - zkM1, Nk_lamk ) # should be positive
     dotTestMax_fromhkM1hk = np.dot( yk - a_tan, N_tan ) # should be positive


