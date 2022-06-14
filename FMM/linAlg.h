/*
USEFUL LINEAR ALGEBRA COMPUTATIONS
*/
#pragma once
#include <math.h>

double l2norm(double x[])
{
    double result;
    result = 0.0;
    result += sqrt( pow(x[0], 2) + pow(x[1], 2)  );
    return result;
}

double dotProd(double x[], double y[])
{
    double result;
    result = 0.0;
    result += x[0]*y[0] + x[1]*y[1];
    return x[0]*y[0] + x[1]*y[1];
}

void scalar_times_2vec(double alpha, double x[], double output[])
{
    output[0] = alpha*x[0];
    output[1] = alpha*x[1];
}

void vec2_addition(double x[], double y[], double output[])
{
    output[0] = x[0] - y[0];
    output[1] = x[1] - y[1];
}

void vec2_substraction(double x[], double y[], double output[])
{
    output[0] = x[0] - y[0];
    output[1] = x[1] - y[1];
}
