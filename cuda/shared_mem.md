## Why shared memory 

Use the example of matrix inner product. 

`
for (int k = 0; k < Width; ++k )
   Pvalue + = d_M[Row*Width+k]*d_N[k*Width+COl]
`

For each two floating point operation, i.e., multiply and addition, we will have to fetch 
