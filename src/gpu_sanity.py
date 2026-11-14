"""Phase 0 GPU sanity check: CUDA visible, bf16 matmul, bitsandbytes 4-bit linear."""
import torch, time
print("torch", torch.__version__, "cuda build", torch.version.cuda, "available", torch.cuda.is_available())
d = torch.device("cuda"); print("device", torch.cuda.get_device_name(0), "driver-capability", torch.cuda.get_device_capability(0))
a = torch.randn(8192, 8192, device=d, dtype=torch.bfloat16); torch.cuda.synchronize(); t = time.time()
for _ in range(20): b = a @ a
torch.cuda.synchronize(); print("bf16 matmul TFLOP/s %.0f" % (20 * 2 * 8192**3 / (time.time() - t) / 1e12))
import bitsandbytes as bnb
lin = bnb.nn.Linear4bit(1024, 1024, compute_dtype=torch.bfloat16, quant_type="nf4").to(d)
print("bnb 4bit out", tuple(lin(torch.randn(4, 1024, device=d, dtype=torch.bfloat16)).shape))
print("sdpa ok", torch.nn.functional.scaled_dot_product_attention(*(torch.randn(1, 8, 128, 64, device=d, dtype=torch.bfloat16),) * 3).shape)
print("SANITY_OK")
