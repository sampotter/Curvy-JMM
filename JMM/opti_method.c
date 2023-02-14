

/*
Optimization methods for the 2D FMM
*/

#include "opti_method.h"
#include "linAlg.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

void linearInterpolation(double param, double from[2], double to[2], double interpolation[2]){
  // useful for xlambda = (1-lambda)*x0 + lambda*x1
  double coeffrom[2], coefto[2];
  scalar_times_2vec(1-param, from, coeffrom);
  scalar_times_2vec(param, to, coefto);
  vec2_addition(coeffrom, coefto, interpolation);
}

void der_linearInterpolation(double param, double from[2], double to[2], double der_interpolation[2]){
  // derivative with respect of lambda of (1-lambda)*x0 + lambda*x1
  vec2_subtraction(to, from, der_interpolation);
}

void hermite_interpolationSpatial(double param, double from[2], double to[2], double grad_from[2], double grad_to[2], double interpolation[2]){
  // general hermite interpolation evaluated at param for the boundary
  double param2, param3;
  double coef_0[2], coef_1[2], coef_grad0[2], coef_grad1[2];
  param2 = param*param;
  param3 = param2*param;
  scalar_times_2vec(2*param3 - 3*param2 + 1, from, coef_0);
  scalar_times_2vec(param3 - 2*param2 + param, grad_from, coef_grad0);
  scalar_times_2vec(-2*param3 + 3*param2, to, coef_1);
  scalar_times_2vec(param3 - param2, grad_to, coef_grad1);
  double sumpoints[2], sumgrads[2];
  vec2_addition(coef_0, coef_1, sumpoints);
  vec2_addition(coef_grad0, coef_grad1, sumgrads);
  vec2_addition(sumpoints, sumgrads, interpolation);
}

void grad_hermite_interpolationSpatial(double param, double from[2], double to[2], double grad_from[2], double grad_to[2], double gradient[2]){
  // gradient of the general hermite interpolation evaluated at param for the boundary (i.e. gradBmu)
  double param2;
  double twofrom[2], twoto[2], threefrom[2], twogradfrom[2], threeto[2];
  scalar_times_2vec(2, from, twofrom);
  scalar_times_2vec(-2, to, twoto);
  scalar_times_2vec(-3, from, threefrom);
  scalar_times_2vec(-2, grad_from, twogradfrom);
  scalar_times_2vec(3, to, threeto);
  double sum1[2], sum2[2], sum3[2], sum4[2];
  vec2_addition(twofrom, grad_from, sum1);
  vec2_addition(twoto, grad_to, sum2);
  vec2_addition(threefrom, twogradfrom, sum3);
  vec2_subtraction(threeto, grad_to, sum4);
  double coefparam2[2], coefparam[2];
  vec2_addition(sum1, sum2, coefparam2);
  vec2_addition(sum3, sum4, coefparam);
  double par1[2], par2[2], par3[2];
  scalar_times_2vec(3*param2, coefparam2, par1);
  scalar_times_2vec(2*param, coefparam, par2);
  vec2_addition(par2, grad_from, par3);
  vec2_addition(par1, par3, gradient);
}

double arclength_hermiteSimpson(double a, double b, double from[2], double to[2], double grad_from[2], double grad_to[2]){
  // using simpsons rule to calculate the arclength for the parameter being from a to b
  // uses grad_hermite_interpolationSpatial of course
  double gradient_a[2], gradient_mid[2], gradient_b[2], norm_a, norm_mid, norm_b;
  grad_hermite_interpolationSpatial(a, from, to, grad_from, grad_to, gradient_a);
  grad_hermite_interpolationSpatial((a+b)/2, from, to, grad_from, grad_to, gradient_mid);
  grad_hermite_interpolationSpatial(b, from, to, grad_from, grad_to, gradient_b);
  norm_a = l2norm(gradient_a);
  norm_mid = l2norm(gradient_mid);
  norm_b = l2norm(gradient_b);
  return (1/6)*(norm_a + 4*norm_mid + norm_b);
}

double hermite_interpolationT(double param, double xA[2], double xB[2], double TA, double TB, double gradA[2], double gradB[2]){
  // hermite interpolation for the value of the eikonal
  double param2, param3;
  param2 = param*param;
  param3 = param2*param;
  double coef_gradA[2], coef_gradB[2], sumgrads[2], xBminxA[2];
  scalar_times_2vec(param3 - 2*param2 + param, gradA, coef_gradA);
  scalar_tiems_2vec(param3 - param2, gradB, coef_gradB);
  vec2_addition(coef_gradA, coef_gradB, sumgrads);
  vec2_subtraction(xB, xA, xBminxA);
  return (2*param3 - 3*param2 + 1)*TA + (-2*param3 + 3*param2)*TB + dotProd(xBminxA, sumgrads);
}

double der_hermite_interpolationT(double param, double xA[2], double xB[2], double TA, double TB, double gradA[2], double gradB[2]){
  // derivative with respect of param for the hermite interpolation for the value of the eikonal
  double param2;
  param2 = param*param;
  double xBminxA[2], gradAplusgradB[2], twogradA[2], twogradAplusgradB[2];
  vec2_subtraction(xB, xA, xBminxA);
  vec2_addition(gradA, gradB, gradAplusgradB);
  scalar_times_2vec(2, gradA, twogradA);
  vec2_addition(twogradA, gradB, twogradAplusgradB);
  double dotProd1, dotProd2, dotProd3;
  dotProd1 = dotProd(xBminxA, gradAplusgradB);
  dotProd2 = dotProd(xBminxA, twogradAplusgradB);
  dotProd3 = dotProd(xBminxA, gradA);
  // put everything together
  return (6*TA - 6*TB + 3*dotProd1)*param2 + (-6*TA + 6*TB - 2*dotProd2)*param + dotProd3;
}



double der_fromEdge(double lambda, double T0, double grad0[2], double B0[2], double T1, double grad1[2], double B1[2], double x0[2], double x1[2], double xHat[2], double indexRef) {
  // derivative with respect of lambda from the function to minimize for the update in which the
  // segment x0x1 is on the boundary but xHat if fully contained in a region with index indexRef
  // segments x0xHat and x1xHat are fully contained in a region 
  double xLam[2], gradxLam[2], der_Tlam, xHatminxLam[2], normxHatminxLam;
  hermite_interpolationSpatial(lambda, x0, x1, B0, B1, xLam);
  grad_hermite_interpolationSpatial(lambda, x0, x1, B0, B1, gradxLam);
  der_Tlam = der_hermite_interpolationT(lambda, x0, x1, T0, T1, grad0, grad1);
  vec2_subtraction(xLam, xHat, xHatminxLam);
  normxHatminxLam = l2norm(xHatminxLam);
  // Putting everything together
  return der_Tlam + indexRef*dotProd(xHatminxLam, gradxLam)/normxHatminxLam;
}

double backTr_fromEdge(double alpha0, double d, double lambda, double T0, double grad0[2], double B0[2], double T1, double grad1[2], double B1[2], double x0[2], double x1[2], double xHat[2], double indexRef){
  // backtracking method for projected gradient descent from updates from the edge of the domain
  double f_prev, f_cur, alpha;
  int i = 0;
  alpha = alpha0;
  // EVALUATING THE OBJECTIVE FUNCTION
  f_prev = fobjective_fromEdge(lambda, T0, grad0, B0, T1, grad1, B1, x0, x1, xHat, indexRef);
  f_cur = fobjective_fromEdge(lambda - alpha*d, T0, grad0, B0, T1, grad1, B1, x0, x1, xHat, indexRef);
  while(f_prev <= f_cur & i < 10){
    alpha = alpha*0.5;
    f_cur = fobjective_fromEdge(lambda - alpha*d, T0, grad0, B0, T1, grad1, B1, x0, x1, xHat, indexRef);
    i ++;
  }
  return alpha;
}

double fobjective_fromEdge(double lambda, double T0, double grad0[2], double B0[2], double T1, double grad1[2], double B1[2], double x0[2], double x1[2], double xHat[2], double indexRef){
  double lambda3, lambda2;
  lambda2 = lambda*lambda;
  lambda3 = lambda2*lambda;
  double x1Minx0[2], B0PlusB1[2], B1Plus2B0[2], twoB0[2], grad0Plusgrad1[2], twoGrad0PlusGrad1[2], twoGrad0[2];
  double lamB0[2], x0MinxHat[2];
  // first time we gather terms
  vec2_subtraction(x1, x0, x1Minx0);
  vec2_addition(B0, B1, B0PlusB1);
  scalar_times_2vec(2, B0, twoB0);
  vec2_addition(B1, twoB0, B1Plus2B0);
  vec2_addition(grad0, grad1, grad0Plusgrad1);
  scalar_times_2vec(2, grad0, twoGrad0);
  vec2_addition(twoGrad0, grad1, twoGrad0PlusGrad1);
  scalar_times_2vec(lambda, B0, lamB0);
  vec2_subtraction(x0, xHat, x0MinxHat);
  // second time gathering terms
  double dotProd1, dotProd2, twox0Minx1[2], threex0Minx1[2];
  dotProd1 = dotProd(x1Minx0, grad0Plusgrad1);
  dotProd2 = dotProd(x1Minx0, twoGrad0PlusGrad1);
  scalar_times_2vec(-2, x1Minx0, twox0Minx1);
  scalar_times_2vec(-3, x1Minx0, threex0Minx1);
  // third time gathering terms
  double coef_lam3_2[2], coef_lam2_2[2], coef_lam_2[2];
  vec2_addition(twox0Minx1, B0PlusB1, coef_lam3_2);
  vec2_addition(threex0Minx1, B1Plus2B0, coef_lam2_2);
  scalar_times_2vec(lambda, B0, coef_lam_2);
  // fourth time gathering terms
  double lam3_2[2], lam2_2[2], rest1_2[2], rest2_2[2];
  scalar_times_2vec(lambda3, coef_lam3_2, lam3_2);
  scalar_times_2vec(lambda2, coef_lam2_2, lam2_2);
  vec2_addition(lamB0, x0MinxHat, rest2_2);
  vec2_subtraction(lam3_2, lam2_2, rest1_2);
  // fifth time gathering terms
  double xHatMinxLam[2], norm1, boundaryPart, tLamPart, dotProd4;
  vec2_addition(rest1_2, rest2_2, xHatMinxLam);
  dotProd4 = dotProd(x1Minx0, grad0);
  norm1 = l2norm(xHatMinxLam);
  tLamPart = 2*T0*lambda3 - 2*T1*lambda3 + lambda3*dotProd1 -3*T0*lambda2 + 3*T1*lambda2 - lambda2*dotProd2 + lambda*dotProd4 + T0;
  return tLamPart + indexRef*norm1;
}


double projectedGradient_fromEdge(double lambda0, double T0, double grad0[2], double B0[2], double T1, double grad1[2], double B1[2], double x0[2], double x1[2], double xHat[2], double tol, double maxIter, double indexRef){
  // projected gradient descent for an update in which the segment x0x1 is on the boundary but xHat
  // if fully contained in a region with index indexRef
  double grad_cur, grad_prev, step, alpha, lam_prev, lam_cur, test;
  int i;
  i = 1;
  alpha = 0.25;
  lam_prev = lambda0;
  grad_cur = der_fromEdge(lambda0, T0, grad0, B0, T1, grad1, B1, x0, x1, xHat, indexRef);
  grad_prev = der_fromEdge(lambda0, T0, grad0, B0, T1, grad1, B1, x0, x1, xHat, indexRef);
  if(fabs(grad_cur) > tol){
    test = lam_prev - alpha*grad_cur;
  }
  else{
    test = lam_prev;
  }
  if(test>1){
    lam_cur = 1;
  }
  else if(test<0){
    lam_cur = 0;
  }
  else{
    lam_cur = test;
  }
  grad_cur = der_fromEdge(lam_cur, T0, grad0, B0, T1, grad1, B1, x0, x1, xHat, indexRef);

  while(i<maxIter & fabs(grad_cur)>tol & fabs(lam_cur - lam_prev)>0) {
    alpha = backTr_fromEdge(0.25, grad_cur, lam_cur, T0, grad0, B0, T1, grad1, B1, x0, x1, xHat, indexRef);
    test = lam_cur - alpha*grad_cur;
    if(test<0){
      test = 0;
    }
    if(test>1){
      test = 1;
    }
    grad_prev = grad_cur;
    lam_prev = lam_cur;
    lam_cur = test;
    grad_cur = der_fromEdge(lam_cur, T0, grad0, B0, T1, grad1, B1, x0, x1, xHat, indexRef);
    i ++;
  }
  
  return lam_cur;
}

double der_freeSpace(double lambda, double TA, double gradA[2], double TB, double gradB[2], double xA[2], double xB[2], double xHat[2], double indexRef){
  double lambda2;
  lambda2 = lambda*lambda;
  // first time we gather terms
  double  xBminxA[2], gradAplusgradB[2], twogradA[2], twogradAplusgradB[2], xHatMinxA[2];
  vec2_subtraction(xB, xA, xBminxA);
  vec2_addition(gradA, gradB, gradAplusgradB);
  scalar_times_2vec(2, gradA, twogradA);
  vec2_addition(twogradA, gradB, twogradAplusgradB);
  vec2_subtraction(xHat, xA, xHatMinxA);
  // second time we gather terms
  double dotProd1, dotProd2, dotProd3, lamxBminxA[2], disxlam[2], dotProd4;
  dotProd1 = dotProd(xBminxA, gradAplusgradB);
  dotProd2 = dotProd(xBminxA, twogradAplusgradB);
  dotProd3 = dotProd(xBminxA, gradA);
  scalar_times_2vec(lambda, xBminxA, lamxBminxA);
  vec2_subtraction(xHatMinxA, lamxBminxA, disxlam);
  dotProd4 = dotProd(xBminxA, disxlam);
  // third time we gather terms
  double tLamPart, rayPart;
  tLamPart = (6*TA - 6*TB + 3*dotProd1)*lambda2 + (-6*TA + 6*TB - 2*dotProd2)*lambda + dotProd3;
  rayPart = indexRef*(dotProd4)/l2norm(disxlam);
  return tLamPart - rayPart;
}

double backTr_freeSpace(double alpha0, double d, double lambda, double TA, double gradA[2], double TB, double gradB[2], double xA[2], double xB[2], double xHat[2], double indexRef){
  double f_prev, f_cur, alpha;
  int i = 0;
  alpha = alpha0;
  // EVALUATING THE OBJECTIVE FUNCTION
  f_prev = fobjective_freeSpace(lambda, TA, gradA, TB, gradB, xA, xB, xHat, indexRef);
  f_cur = fobjective_freeSpace(lambda - alpha*d, TA, gradA, TB, gradB, xA, xB, xHat, indexRef);
  while(f_prev <= f_cur & i < 10){
    alpha = alpha*0.5;
    f_cur = fobjective_freeSpace(lambda - alpha*d, TA, gradA, TB, gradB, xA, xB, xHat, indexRef);
    i ++;
  }
  return alpha;
}

double fobjective_freeSpace(double lambda, double TA, double gradA[2], double TB, double gradB[2], double xA[2], double xB[2], double xHat[2], double indexRef){
  double lambda2, lambda3;
  lambda2 = lambda*lambda;
  lambda3 = lambda2*lambda;
  // first time we gather terms
  double xBminxA[2], gradAplusgradB[2], twogradA[2], twogradAplusgradB[2], lamxBminxA[2], xHatminxA[2];
  vec2_subtraction(xB, xA, xBminxA);
  vec2_addition(gradA, gradB, gradAplusgradB);
  scalar_times_2vec(2, gradA, twogradA);
  vec2_addition(twogradA, gradB, twogradAplusgradB);
  scalar_times_2vec(lambda, xBminxA, lamxBminxA);
  vec2_subtraction(xHat, xA, xHatminxA);
  // second time we gather terms
  double dotProd1, dotProd2, dotProd3, disxlam[2], norm1;
  dotProd1 = dotProd(xBminxA, gradAplusgradB);
  dotProd2 = dotProd(xBminxA, twogradAplusgradB);
  dotProd3 = dotProd(xBminxA, gradA);
  vec2_subtraction(xHatminxA, lamxBminxA, disxlam);
  norm1 = l2norm(disxlam);
  return (2*TA - 2*TB + dotProd1)*lambda3 + (-3*TA + 3*TB - dotProd2)*lambda2 + dotProd3*lambda + TA + indexRef*norm1;
}

double projectedGradient_freeSpace(double lambda0, double lambdaMin, double lambdaMax, double TA, double gradA[2], double TB, double gradB[2], double xA[2], double xB[2], double xHat[2], double tol, double maxIter, double indexRef){
  // two point optimization problem. xA and xHat are on the boundary and xB is fully contained in one region.
  // With usual notation xA could be either x0 or x1 and xB could be either x0 or x1 (this is more abstract)
  // THIS IS A PROJECTED GRADIENT DESCENT METHOD
  double grad_cur, grad_prev, step, alpha, lam_prev, lam_cur, test;
  int i =1;
  alpha = 1;
  lam_prev = lambda0;
  grad_cur = der_freeSpace(lambda0, TA, gradA, TB, gradB, xA, xB, xHat, indexRef);
  grad_prev = grad_cur;
  if(fabs(grad_cur) > tol){
    test = lam_prev - alpha*grad_cur;
  }
  else{
    test = lam_prev;
  }
  if(test>lambdaMax){
    test = lambdaMax;
  }
  if(test<lambdaMin){
    test = lambdaMin;
  }
  lam_cur = test;
  grad_cur = der_freeSpace(lam_cur, TA, gradA, TB, gradB, xA, xB, xHat, indexRef);

  while( i<maxIter & fabs(grad_cur)>tol & fabs(lam_cur - lam_prev)>0){
    alpha = backTr_freeSpace(1, grad_cur, lam_cur, TA, gradA, TB, gradB, xA, xB, xHat, indexRef);
    //printf("\n\nIteration %d\n", i);
    //printf("Step size %lf   with direction  %lf, hence change is %lf\n", alpha, -grad_cur, -alpha*grad_cur);
    test = lam_cur - alpha*grad_cur;
    if(test > lambdaMax){
      test = lambdaMax;
    }
    if(test < lambdaMin){
      test = lambdaMin;
    }

    grad_prev = grad_cur;
    lam_prev = lam_cur;
    lam_cur = test;
    grad_cur = der_freeSpace(lam_cur, TA, gradA, TB, gradB, xA, xB, xHat, indexRef);
    //printf("Iteration %d   with lam_prev %lf  and lam_cur %lf   with objective value: %lf   and derivative  %lf \n\n\n", i, lam_prev, lam_cur, fobjective_freeSpace(lam_cur, TA, gradA, TB, gradB, xA, xB, xHat, indexRef), grad_cur);
    
    i++;
  }

  return lam_cur;
}

void grad_twoStep(double gradient[2], double lambda, double mu, double T0, double grad0[2], double T1, double grad1[2], double x0[2], double x1[2], double x2[2], double xHat[2], double B0[2], double B2[2], double indexRef_01, double indexRef_02) {
  // gradient for the function to minimize for a two step update (when there is a change in region)
  double mu2, mu3, lambda2;
  mu2 = mu*mu;
  mu3 = mu2*mu;
  lambda2 = lambda*lambda;
  /////// partial with respect to lambda
  // first time gathering terms
  double x1Minx0[2], x0InxLamMinxMu[2], x1inxLamMinxMu[2], B0inxLamMinxMu[2], x2InxLamMinxMu[2], B2inxLamMinxMu[2];
  vec2_subtraction(x1, x0, x1Minx0);
  scalar_times_2vec(-lambda-2*mu3 + 3*mu2, x0, x0InxLamMinxMu);
  scalar_times_2vec(lambda, x1, x1inxLamMinxMu);
  scalar_times_2vec(mu3 - 2*mu2 + mu, B0, B0inxLamMinxMu);
  scalar_times_2vec(-2*mu3 + 3*mu2, x2, x2InxLamMinxMu);
  scalar_times_2vec(mu3 - mu2, B2, B2inxLamMinxMu);
  // second time gatherieng terms
  double sum1[2], sum2[2], sum3[2], xLamMinxMu[2], t, normxLamMinxMu, coefgrad0[2], coefgrad1[2], sumgrads[2], dot1;
  vec2_addition(x0InxLamMinxMu, x1inxLamMinxMu, sum1);
  vec2_addition(B0inxLamMinxMu, x2InxLamMinxMu, sum2);
  vec2_addition(sum2, B2inxLamMinxMu, sum3);
  vec2_subtraction(sum1, sum3, xLamMinxMu);
  t = dotProd(x1Minx0, xLamMinxMu);
  normxLamMinxMu = l2norm(xLamMinxMu);
  scalar_times_2vec(3*lambda2 - 4*lambda + 1, grad0, coefgrad0);
  scalar_times_2vec(3*lambda2 - 2*lambda, grad1, coefgrad1);
  vec2_addition(coefgrad0, coefgrad1, sumgrads);
  dot1 = dotProd(x1Minx0, sumgrads);
  // then the partial is
  gradient[0] =(6*lambda2 - 6*lambda)*T0 + (-6*lambda2 + 6*lambda)*T1 + dot1 + indexRef_01*t/normxLamMinxMu;
  /////// partial with respect to mu
  // first time gathering terms
  double der_coefx0[2], der_coefB0[2], der_coefx2[2], der_coefB2[2];
  scalar_times_2vec(-6*mu2 + 6*mu, x0, der_coefx0);
  scalar_times_2vec(-3*mu2 + 4*mu - 1, B0, der_coefB0);
  scalar_times_2vec(6*mu2 - 6*mu, x2, der_coefx2);
  scalar_times_2vec(-3*mu2 + 2*mu, B2,  der_coefB2);
  // second time gathering terms
  double coefx0[2], coefB0[2], coefx2[2], coefB2[2];
  scalar_times_2vec(-2*mu3 + 3*mu2 - 1, x0, coefx0);
  scalar_times_2vec(-mu3 + 2*mu2 - mu, B0, coefB0);
  scalar_times_2vec(2*mu3 - 3*mu2, x2, coefx2);
  scalar_times_2vec(-mu3 + mu2, B2, coefB2);
  // third time gathering terms
  double der_sum1[2], der_sum2[2], derMuxMu[2], sum4[2], sum5[2], sum6[2], xLamMinxHat[2], normxLamMinxHat;
  vec2_addition(der_coefx0, der_coefB0, der_sum1);
  vec2_addition(der_coefx2,  der_coefB2, der_sum2);
  vec2_addition(der_sum1, der_sum2, derMuxMu);
  vec2_addition(xHat, coefx0, sum4);
  vec2_addition(coefB0, coefx2, sum5);
  vec2_addition(sum5, coefB2, sum6);
  vec2_addition(sum4, sum6, xLamMinxHat);
  normxLamMinxHat = l2norm(xLamMinxHat);
  // fourth time gathering terms
  double t1, t2;
  t1 = dotProd( derMuxMu, xLamMinxMu);
  t2 = dotProd( derMuxMu, xLamMinxHat);
  // everything together
  gradient[1] = indexRef_01*t1/normxLamMinxMu + indexRef_02*t2/normxLamMinxHat;
}


double backTr_TwoStep(double alpha0, double d[2], double lambda, double mu, double T0, double grad0[2], double T1, double grad1[2], double x0[2], double x1[2], double x2[2], double xHat[2], double B0[2], double B2[2], double indexRef_01, double indexRef_02) {
  // backtracking to compute a step length in the two step update
  double f_prev, f_cur, alpha;
  int i = 0;
  alpha = alpha0;
  // EVALUATING THE OBJECTIVE FUNCTION
  f_prev = fobjective_TwoStep(lambda, mu, T0, grad0, T1, grad1, x0, x1, x2, xHat, B0, B2, indexRef_01, indexRef_02);
  //printf("Objective function before %lf  with lambda %lf  and mu  %lf\n", f_prev, lambda, mu);
  f_cur = fobjective_TwoStep(lambda - alpha*d[0], mu - alpha*d[1], T0, grad0, T1, grad1, x0, x1, x2, xHat, B0, B2, indexRef_01, indexRef_02);
  while(f_prev <= f_cur & i < 10 ){
    alpha = alpha*0.5;
    f_cur = fobjective_TwoStep(lambda - alpha*d[0], mu - alpha*d[1], T0, grad0, T1, grad1, x0, x1, x2, xHat, B0, B2, indexRef_01, indexRef_02);
    i ++;
  }
  if (f_prev <= f_cur){
    alpha = 0;
  }
  //printf("Objective function adter back tracking  %lf\n", fobjective_TwoStep(lambda - alpha*d[0], mu - alpha*d[1], T0, grad0, T1, grad1, x0, x1, x2, xHat, B0, B2, indexRef_01, indexRef_02) );
  //printf("with lambda %lf  and mu %lf\n", lambda-alpha*d[0], lambda-alpha*d[1]);
  return alpha;
}

double fobjective_TwoStep(double lambda, double mu, double T0, double grad0[2], double T1, double grad1[2], double x0[2], double x1[2], double x2[2], double xHat[2], double B0[2], double B2[2], double indexRef_01, double indexRef_02){
  // objective function for a two step update
  double lambda2, lambda3, mu2, mu3;
  lambda2 = lambda*lambda;
  lambda3 = lambda2*lambda;
  mu2 = mu*mu;
  mu3 = mu2*mu;
  // firt time gathering terms
  double x1Minx0[2], coefgrad0[2], coefgrad1[2], sumgrads[2], dotProd1;
  vec2_subtraction(x1, x0, x1Minx0);
  scalar_times_2vec(lambda3 - 2*lambda2 + lambda, grad0, coefgrad0);
  scalar_times_2vec(lambda3 - lambda2, grad1, coefgrad1);
  vec2_addition(coefgrad0, coefgrad1, sumgrads);
  dotProd1 = dotProd(x1Minx0, sumgrads);
  // second time gathering terms
  double x0InxLamMinxMu[2], x1inxLamMinxMu[2], B0inxLamMinxMu[2], x2InxLamMinxMu[2], B2inxLamMinxMu[2];
  scalar_times_2vec(-lambda-2*mu3 + 3*mu2, x0, x0InxLamMinxMu);
  scalar_times_2vec(lambda, x1, x1inxLamMinxMu);
  scalar_times_2vec(-mu3 + 2*mu2 - mu, B0, B0inxLamMinxMu);
  scalar_times_2vec(2*mu3 - 3*mu2, x2, x2InxLamMinxMu);
  scalar_times_2vec(-mu3 + mu2, B2, B2inxLamMinxMu);
  // third time gatherieng terms
  double sum1[2], sum2[2], sum3[2], xLamMinxMu[2], t, normxLamMinxMu, dot1;
  vec2_addition(x0InxLamMinxMu, x1inxLamMinxMu, sum1);
  vec2_addition(B0inxLamMinxMu, x2InxLamMinxMu, sum2);
  vec2_addition(sum2, B2inxLamMinxMu, sum3);
  vec2_addition(sum1, sum3, xLamMinxMu);
  normxLamMinxMu = l2norm(xLamMinxMu);
  // fourth time gathering terms
  double coefx0[2], coefB0[2], coefx2[2], coefB2[2];
  scalar_times_2vec(-2*mu3 + 3*mu2 - 1, x0, coefx0);
  scalar_times_2vec(-mu3 + 2*mu2 - mu, B0, coefB0);
  scalar_times_2vec(2*mu3 - 3*mu2, x2, coefx2);
  scalar_times_2vec(-mu3 + mu2, B2, coefB2);
  // fifth time gathering terms
  double sum4[2], sum5[2], sum6[2], xLamMinxHat[2], normxLamMinxHat;
  vec2_addition(xHat, coefx0, sum4);
  vec2_addition(coefB0, coefx2, sum5);
  vec2_addition(sum5, coefB2, sum6);
  vec2_addition(sum4, sum6, xLamMinxHat);
  normxLamMinxHat = l2norm(xLamMinxHat);
  
  return (2*lambda3 - 3*lambda2 + 1)*T0 + (-2*lambda3 + 3*lambda2)*T1 + dotProd1 + indexRef_01*normxLamMinxMu + indexRef_02*normxLamMinxHat;
  
}


void projectedGradient_TwoStep(double optimizers[2], double lambdaMin, double lambdaMax, double muMin, double muMax, double T0, double grad0[2], double T1, double grad1[2], double x0[2], double x1[2], double x2[2], double xHat[2], double B0[2], double B2[2], double indexRef_01, double indexRef_02, double tol, int maxIter) {
  // projected gradient descent for a two step update (when the index of refraction changes)
  double grad_cur[2], grad_prev[2], step, alpha, optimizers_prev[2], optimizers_cur[2], test[2], difStep[2];
  int i = 1;
  alpha = 0.1;
  optimizers[0] = lambdaMax;
  optimizers[1] = muMax;
  // compute the gradient
  grad_twoStep(grad_cur, optimizers[0], optimizers[1], T0, grad0, T1, grad1, x0, x1, x2, xHat, B0, B2, indexRef_01, indexRef_02);
  grad_prev[0] = grad_cur[0];
  grad_prev[1] = grad_cur[1];
  if (l2norm(grad_cur) > tol){
    test[0] = optimizers[0] - alpha*grad_cur[0];
    test[1] = optimizers[1] - alpha*grad_cur[1];
  }
  else{
    test[0] = optimizers[0];
    test[1] = optimizers[1];
  }
  if( test[0] > lambdaMax){
    test[0] = lambdaMax;
  }
  if(test[1] > muMax){
    test[1] = muMax;
  }
  if(test[0] < lambdaMin){
    test[0] = lambdaMin;
  }
  if(test[1] < muMin){
    test[1] = muMin;
  }
  // start the iteration
  optimizers_cur[0] = test[0];
  optimizers_cur[1] = test[1];
  grad_twoStep(grad_cur, optimizers_cur[0], optimizers_cur[1], T0, grad0, T1, grad1, x0, x1, x2, xHat, B0, B2, indexRef_01, indexRef_02);
  vec2_subtraction(optimizers_prev, optimizers_cur, difStep);
  while(i < maxIter & l2norm(grad_cur) > tol & l2norm(difStep) > 0){
    //printf("\n\nIteration %d\n", i);
    alpha = backTr_TwoStep(0.1, grad_cur, optimizers_cur[0], optimizers_cur[1], T0, grad0, T1, grad1, x0, x1, x2, xHat, B0, B2, indexRef_01, indexRef_02);
    //printf("Step size %lf  with direction  %lf  %lf, hence the change is  %lf   %lf\n", alpha, -grad_cur[0], -grad_cur[1], -alpha*grad_cur[0], - alpha*grad_cur[1]);
    test[0] = optimizers_cur[0] - alpha*grad_cur[0];
    test[1] = optimizers_cur[1] - alpha*grad_cur[1];
    //printf("Values before projecting back  %lf   %lf\n", test[0], test[1]);
    // project back if neccesary
    if( test[0] > lambdaMax){
      test[0] = lambdaMax;
    }
    if(test[1] > muMax){
      test[1] = muMax;
    }
    if(test[0] < lambdaMin){
      test[0] = lambdaMin;
    }
    if(test[1] < muMin){
      test[1] = muMin;
    }
    // if there is no better function value don't update
    if( fobjective_TwoStep(optimizers_cur[0], optimizers_cur[1], T0, grad0, T1, grad1, x0, x1, x2, xHat, B0, B2, indexRef_01, indexRef_02) < fobjective_TwoStep(test[0], test[1], T0, grad0, T1, grad1, x0, x1, x2, xHat, B0, B2, indexRef_01, indexRef_02) ) {
      test[0] = optimizers_cur[0];
      test[1] = optimizers_cur[1];
    }
    // update
    grad_prev[0] = grad_cur[0];
    grad_prev[1] = grad_cur[1];
    optimizers_prev[0] = optimizers_cur[0];
    optimizers_prev[1] = optimizers_cur[1];
    optimizers_cur[0] = test[0];
    optimizers_cur[1] = test[1];
    vec2_subtraction(optimizers_prev, optimizers_cur, difStep);
    grad_twoStep(grad_cur, optimizers_cur[0], optimizers_cur[1], T0, grad0, T1, grad1, x0, x1, x2, xHat, B0, B2, indexRef_01, indexRef_02);
    //printf("Iteration %d  with lambda_prev   %lf   and lambda_cur  %lf\n", i, optimizers_prev[0], optimizers_cur[0]);
    //printf("Iteration %d  with mu_prev   %lf   and mu_cur  %lf\n", i, optimizers_prev[1], optimizers_cur[1]);
    //printf("Objective value   %lf    and gradient %lf  %lf \n", fobjective_TwoStep(optimizers_cur[0], optimizers_cur[1], T0, grad0, T1, grad1, x0, x1, x2, xHat, B0, B2, indexRef_01, indexRef_02), grad_cur[0], grad_cur[1]);
    i ++;
  }
  optimizers[0] = optimizers_cur[0];
  optimizers[1] = optimizers_cur[1];
}


double tofMu(double xA[2], double xB[2], double xmu[2], double Bmu[2]){
  // auxiliary function defined in notes
  // t(mu) = dot( xmu - x0, Bmu_perp)/dot(x1 - x0, Bmu_perp)
  double Bmu_perp[2], xmuMinxA[2], xBMinxA[2];
  Bmu_perp[0] = Bmu[1];
  Bmu_perp[1] = - Bmu[0];
  vec2_subtraction(xmu, xA, xmuMinxA);
  vec2_subtraction(xB, xA, xBMinxA);
  return dotProd(xmuMinxA, Bmu_perp)/dotProd(xBMinxA, Bmu_perp);
}

double der_tofMu(double xA[2], double xB[2], double xmu[2], double Bmu[2], double grad_Bmu[2]){
  // derivative with respect to lambda of t(mu) defined above
  double grad_Bmu_perp[2], xBminxA[2], xmuMinxA[2], Bmu_perp[2], top, bottom;
  grad_Bmu_perp[0] = grad_Bmu[1];
  grad_Bmu_perp[1] = -grad_Bmu[0];
  Bmu_perp[0] = Bmu[1];
  Bmu_perp[1] = -Bmu[0];
  vec2_subtraction(xmu, xA, xmuMinxA);
  vec2_subtraction(xB, xA, xBminxA);
  top = dotProd( xmuMinxA, grad_Bmu_perp)*dotProd(xBminxA, Bmu_perp) - dotProd(xBminxA, grad_Bmu_perp)*dotProd(muMinxA, Bmu_perp);
  bottom = (dotProd(xBminxA, Bmu_perp))*(dotProd(xBminxA, Bmu_perp));
  return top/bottom;
}

double der_directCr(double mu, double mu2, double t, double t2, double coef3xmu[2], double coef2xmu[2], double BHat[2], double xA[2], double xB[2], double xHat[2], double TA, double TB, double gradA[2], double gradB[2]){
  // derivative of the objective function for an update with a straight line and a creeping ray part
  // with respect to mu
  // uses der_tofMu (because of the chain rule)
  double dert;
  dert = der_tofMu(xA, xB, xmu, Bmu, 
  double xBminxA[2], coefgradA[2], coefgradB[2];
  vec2_subtraction(xB, xA, xBminxA);
  scalar_times_2vec(3*t2 - 4*t + 1, gradA, coefgradA);
  scalar_times_2vec(3*t2 - 2*t, gradB, coefgradB);
  double part1;
  part1 = T0*(6*t2 - 6*t)*
  
}

double fobjective_directCr(double mu, double xA[2], double xB[2], double xHat[2], double xR[2], double TA, double TB, double gradA[2], double gradB[2], double BR[2], double BHat[2], double indexRef){
  // objective function for an update such that it has a straight line part and a creeping ray part
  double t, t2, t3, xmu[2], Bmu[2], mu2, mu3;
  mu2 = mu*mu;
  mu3 = mu2*mu;
  // we compute xmu
  double coef3xmu[2], coef2xmu[2], aux1[2], axu2[2], aux3[2], aux4[2], aux5[2], aux6[2];
  double part3xmu[2], part2xmu[2], aux7[2];
  double twoxHat[2], twoxR[2], threexHat[2], twoBHat[2], threexR[2];
  scalar_times_2vec(2, xHat, twoxHat);
  scalar_times_2vec(2, xR, twoxR);
  scalar_times_2vec(3, xHat, threexHat);
  scalar_times_2vec(2, BHat, twoBHat);
  scalar_times_2vec(3, xR, threexR);
  vec2_addition(twoxHat, BHat, aux1);
  vec2_subtraction(BR, twoxR, aux2);
  vec2_addition(aux1, aux2, coef3xmu); // coefficient of mu**3
  scalar_times_2vec(mu3, coef3xmu, part3xmu);
  vec2_addition(threexHat, twoBHat, aux3);
  vec2_subtraction(threexR, BR, aux4);
  vec2_subtraction(aux4, aux3, coef2xmu); // coefficient of mu**2
  scalar_times_2vec(mu2, coef2xmu, part2xmu);
  scalar_times_2vec(mu, BHat, aux5); // coef mu
  vec2_addition(aux5, xHat, aux6);
  vec2_addition(part3xmu, part2xmu, aux7);
  vec2_addition(aux6, aux7, xmu); // finally compute xmu
  // compute the t's
  t = tofMu(xA, xB, xmu, Bmu);
  t2 = t*t;
  t3 = t2*t;
  // compute xlam
  double xlam[2], coefx0[2], coefx1[2];
  scalar_times_2vec(1-t, xA, coefx0);
  scalar_times_2vec(t, xB, coefx1);
  vec2_addition(coefx0, coefx1, xlam);
  // compute the arc length using Simpson's rule
  double normBHat, part1ghalves[2], part2ghalves[2], sum1ghalves[2], ghalves[2], normghalves;
  double part1g[2], part2g[2], sum1g[2], gmu[2], normgmu;
  normBHat = l2norm(BHat);
  // g(mu/2)
  scalar_times_2vec(3/4*mu2, coef3xmu, part1ghalves);
  scalar_times_2vec(mu, coef2mu, part2ghalves);
  vec2_addition(part2ghalves, BHat, sum1ghalves);
  vec2_addition(part1ghalves, sum1ghalves, ghalves);
  normghalves = l2norm(ghalves);
  // g(mu)
  scalar_times_2vec(3*mu3, coef3xmu, part1g);
  scalar_times_2vec(2*mu, coef2xmu, part2g);
  vec2_addition(part2g, BHat, sum1g);
  vec2_addition(part1g, sum1g, gmu);
  normgmu = l2norm(gmu);
  // xmu minus xlambda
  double xmuMinxlam[2], normxmuMinxlam;
  vec2_subtraction(xmu, xlam, xmuMinxlam);
  normxmuMinxlam = l2norm(xmuMinxlam);
  // compute Tmu
  double xBminxA[2], coefgradA[2], coefgradB[2], sumgrads[2];
  vec2_subtraction(xB, xA, xBminxA);
  scalar_times_2vec(t3 - 2*t2 + t, gradA, coefgradA);
  scalar_times_2vec( t3 - t2, gradB, coefgradB);
  vec2_addition(coefgradA, coefgradB, sumgrads);
  double Tmu;
  Tmu = TA*(2*t3 - 3*t2) + TB(-2*t3 + 3*t2) + dotProd(xBminxA, sumgrads);
  // put everything together
  return Tmu + indexRef*normxmuMinxlam + indexRef/6*( normBHat + 4*normghalves + normgmu  )
  
}

