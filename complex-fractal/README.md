# Julia set

From a complex seed c, compute each pixel noted with a complex position u:
  u = u * c

If the serie diverges, the pixel color is the number of iteration it took to reach infinity.
The longer it took, the brighter is the color.

If the serie doesn't diverge, the pixel color is black.


# Mandelbrot set

There are two type of julia set:
* the one that are connected when u is 0 and the pixel is black
* the one that are disconnected when u is 0 and u = u * c diverged.

For each pixel noted with a complex position c, compute the julia set equation starting with u = 0.

If the serie diverges, the pixel color is the number of iteration it took to reach infinity.
The longer it took, the brighter is the color.

When running [demo](mandelbrot_set.py), right click on the mandelbrot render will draw
the associated julia set with c set to the mouse click position.
