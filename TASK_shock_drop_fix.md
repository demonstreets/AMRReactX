# TASK: 添加液滴粘度/导热系数

在 `/home/cj/my-pele/examples/academic/shock_droplet/inputs` 的 `particles.fuel_sigma = 15.` 之后添加:

```
# Heptane liquid transport properties (for KHRT breakup)
# μ(T) polynomial coefficients (CGS: Poise)
particles.NC7H16_mu = 0.004 0.0 0.0 0.0
# λ(T) polynomial coefficients (CGS: erg/(cm·s·K))
particles.NC7H16_lambda = 120.0 0.0 0.0 0.0
```

改完立即编译运行: `make -j8 && ./PeleC2d.gnu.ex inputs max_step=500`
