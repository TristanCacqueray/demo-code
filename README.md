This repository contains small computer code to render maths equations.

# Examples
```shell
$ ./complex-fractal/julia_set.py --c "(-0.55+0.56j)"
JuliaSet explorer
=================

Click the window to center
Use keyboard arrow to move window, 'a'/'e' to zoom in/out, 'r' to reset view
Use 'qzsd' to change c value or RETURN key to browse known seeds
```
![-0.55+0.56j](render/fractal_julia_set-55.png)

```shell
./complex-fractal/mandelbrot_set.py
MandelbrotSet explorer
======================

Left/right click to zoom in/out, Middle click to draw JuliaSet
Use keyboard arrow to move view and r to reset
```
![mandelbrot set](render/fractal_mandelbrot_set.png)

```shell
./complex-fractal/animation_mandelbrot_zoom.py --size 5 --opencl \
	--color log+sin+lightblue --max_iter 10000 \
	--center "(-1.010164627168485-0.3124969856767653j)" \
	--radius 9.84953164603e-10 --record $(pwd)/zoom --steps 1848
```
![mandelbrot zoom](render/fractal_mandelbrot_set_zoom.gif)


```shell
./bifurcational-fractal/markus_lyapunov.py --seed AB
Markus-Lyapunov explorer
========================

Click the window to center
Use keyboard arrow to move window, 'a'/'e' to zoom in/out, 'r' to reset view
```
![AB](render/fractal_markus_lyapunov-AB.png)
