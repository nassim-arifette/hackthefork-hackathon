"""Measure the quantile-forest SIMD tie-order effect against archived results."""
import os
import subprocess
import sys

disabled = 'AVX512F,AVX512CD,AVX512_SKX,AVX512_CLX,AVX512_CNL,AVX512_ICL'
result = subprocess.run([sys.executable, '/content/verify_migration_colab.py',
    '--output', '/content/advanced-migration-verification-noavx512'],
    env={**os.environ, 'NPY_DISABLE_CPU_FEATURES': disabled},
    capture_output=True, text=True)
print(result.stdout)
print(result.stderr)
print('VERIFICATION_RETURN_CODE', result.returncode)
