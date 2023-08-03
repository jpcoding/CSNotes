## Why shared memory 

Use the example of matrix inner product. 

```
for (int k = 0; k < Width; ++k )
   Pvalue + = d_M[Row*Width+k]*d_N[k*Width+Col]
```

For each calculation (two floating point operations), i.e., multiply and addition, we will have to fetch two floating point number from the device global memeory.The *compute to global memory access (CGMA) ratio* is 1:1.  Say, we have a GPU global memory with 200GB/s bandwithd. with 4 bytes in each single-precision floating-point value, one can expect to load no more than 50 giga operanda per second, simply put, 50GFLOPS. This is far less than the performance of a decent GPU's performanc like 1500 GFLOPS. 
