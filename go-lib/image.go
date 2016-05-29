// Licensed under the Apache License, Version 2.0
package image

import (
    "image"
    "image/png"
    "os"
    //"os/exec"
    "log"
    "fmt"
)

type ImageRender struct {
    Width, Height uint16
    Length uint32
    Data []uint64
    Pixels []uint8
    rgba *image.RGBA
}

func NewImage(w uint16, h uint16) *ImageRender {
    size := uint32(w) * uint32(h)
    buf := make([]uint8, 4 * size)
    data := make([]uint64, size)
    rgba := image.RGBA{buf, 4 * int(w), image.Rect(0, 0, int(w), int(h))}
    return &ImageRender{w, h, size, data, buf, &rgba}
}

func (image ImageRender) String() string {
    return fmt.Sprintf("<ImageRender(%d, %d): %v, %v>", image.Width, image.Height, image.Pixels, image.rgba.Pix)
}

func (image ImageRender) Save(filepath string) {
    if filepath == "" {
        log.Fatal("Can't save without record path")
    }
    outFile, err := os.Create(filepath)
    if err != nil {
        log.Fatal(err)
    }
    defer outFile.Close()
    log.Print("Saving image to: ", filepath)
    png.Encode(outFile, image.rgba)
}
/*
func (image ImageRender) Show() {
    cmd := exec.Command("feh", image.Filepath)
    err := cmd.Start()
    if err != nil {
        log.Fatal(err)
    }
    log.Printf("Waiting for command to finish...")
    err = cmd.Wait()
}
*/


