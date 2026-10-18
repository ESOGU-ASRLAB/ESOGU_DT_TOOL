# Machine and runtime environment

- Recorded: 2026-10-17T23:47:06.050730+03:00
- Hostname: DESKTOP-EN9JDE5
- OS: Windows-11-10.0.26200-SP0
- CPU: Intel64 Family 6 Model 183 Stepping 1, GenuineIntel
- Logical processors: 32
- RAM bytes: 68390989824
- GPU, VRAM, driver: NVIDIA RTX 4000 Ada Generation, 20475 MiB, 596.71
- CUDA information: see `nvidia-smi` summary below.
- Python: 3.12.7 (CPython)
- llama.cpp backend: `C:\Users\matisse\.cache\lm-studio\extensions\backends\llama.cpp-win-x86_64-nvidia-cuda12-avx2-2.55.0\llama-server.exe`
- llama.cpp version: version: 0.6.0-dev (build 1, commit fc9ce6b)
built with Clang 19.1.1 for Windows AMD64
- LM Studio model store: `C:/Users/matisse/.cache/lm-studio/models`
- Docker client/server: 29.1.2 /
- STLC Manager Git commit: `72cdb3daa54fc4e060b207a09cdc74e749f41fb7`
- MongoDB: local `stlc_database` on `127.0.0.1:27017`

## NVIDIA summary

```text
Sat Oct 17 23:47:05 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 596.71                 Driver Version: 596.71         CUDA Version: 13.2     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA RTX 4000 Ada Gene...  WDDM  |   00000000:01:00.0 Off |                  Off |
| 30%   27C    P8              6W /  130W |      11MiB /  20475MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|    0   N/A  N/A           31064    C+G   ...2p2nqsd0c76g0\app\ChatGPT.exe      N/A      |
+-----------------------------------------------------------------------------------------+
```

No credentials, API keys, or passwords are included in this report.
