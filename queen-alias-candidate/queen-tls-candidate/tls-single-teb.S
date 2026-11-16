// ARM64EC-compatible leaf body only; compiled as plain AArch64 code.
// Uses volatile x8/x9, no stack, no calls, no relocations.
// The BCD loader rewrites MOV-from-x18 into its safe current-thread TSD load.
.text
.p2align 2
.globl bcd_tls_single_teb
bcd_tls_single_teb:
  mov x8, x18
  str wzr, [x8, #0x68]
  cmp w0, #64
  b.hs 1f
  add x9, x8, w0, uxtw #3
  ldr x0, [x9, #0x1480]
  ret
1:
  sub w0, w0, #64
  cmp w0, #1024
  b.hs 2f
  ldr x9, [x8, #0x1780]
  cbz x9, 3f
  ldr x0, [x9, w0, uxtw #3]
  ret
2:
  mov w9, #87
  str w9, [x8, #0x68]
3:
  mov x0, xzr
  ret
  nop
