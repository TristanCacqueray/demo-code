// Licensed under the Apache License, Version 2.0
package main

import (
    "../"
    "flag"
)

var (
    show = flag.Bool("show", false, "Display rendered image")
    width = flag.Int("width", 400, "")
    height = flag.Int("height", 400, "")
    record = flag.String("record", "", "Record images to directory")
)


func main() {
    flag.Parse()
    img := image.NewImage(uint16(*width), uint16(*height))

    // Compute exponent map
    for pos := uint32(0); pos < img.Length; pos++ {
        img.Data[pos] = uint64(pos + 1)
    }

    // Colorize
    for pos := uint32(0); pos < img.Length; pos++ {
        pixel_pos := pos * 4
        img.Pixels[pixel_pos + 0] = uint8(128 * (float64(pos % uint32(img.Width)) / float64(img.Width)))
        img.Pixels[pixel_pos + 1] = uint8(100 + (100 * (float64(img.Data[pos]) / float64(img.Length))  * float64(img.Data[pos]) / float64(img.Length)))
        img.Pixels[pixel_pos + 2] = uint8(128 * (float64(pos) / float64(img.Height)) / float64(img.Height))
        /*for idx := uint32(0); idx < 3; idx++ {
            img.Pixels[pixel_pos + idx] = uint8(255 * float64(img.Length) / float64(img.Data[pos]))
        }*/
        img.Pixels[pixel_pos + 3] = 255
    }
    if *record != "" {
        img.Save(*record)
    }
    if *show {
//        img.Show()
    }
}
