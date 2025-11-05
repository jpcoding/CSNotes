#include <iostream>
#include <chrono>
using namespace std;

const int N = 1024;
static double A[N][N], B[N][N], C[N][N];

int main() {
    for(int i=0;i<N;i++)
        for(int j=0;j<N;j++)
            A[i][j] = B[i][j] = 1.0;

    auto run = [&](int block){
        auto start = chrono::high_resolution_clock::now();
        for(int ii=0; ii<N; ii+=block)
            for(int jj=0; jj<N; jj+=block)
                for(int kk=0; kk<N; kk+=block)
                    for(int i=ii; i<ii+block; i++)
                        for(int j=jj; j<jj+block; j++)
                            for(int k=kk; k<kk+block; k++)
                                C[i][j] += A[i][k] * B[k][j];
        auto end = chrono::high_resolution_clock::now();
        return chrono::duration<double, milli>(end-start).count();
    };

    cout << "No blocking (block=1024): " << run(N) << " ms\n";
    cout << "Blocked (block=32):      " << run(32) << " ms\n";
}

