// Licensed under the Apache License, Version 2.0
package main

import (
    "fmt"
    "math"
    //"time"
    "github.com/BurntSushi/xgb"
    "github.com/BurntSushi/xgb/xproto"
    "flag"
)

var (
    width = flag.Int("width", 200, "")
    height = flag.Int("height", 200, "")
)

func main() {
    flag.Parse()

    X, err := xgb.NewConn()
    if err != nil {
        fmt.Println(err)
        return
    }

    setup := xproto.Setup(X)
    screen := setup.DefaultScreen(X)

    wid, _ := xproto.NewWindowId(X)

    xproto.CreateWindow(X, screen.RootDepth, wid, screen.Root,
        0, 0, uint16(*width), uint16(*height), 0,
        xproto.WindowClassInputOutput, screen.RootVisual, 0, []uint32{})

    foreground, _ := xproto.NewGcontextId(X)
    drawable := xproto.Drawable(wid)

    xproto.CreateGCChecked(X, foreground, drawable, xproto.GcForeground | xproto.GcGraphicsExposures,
        []uint32{screen.BlackPixel, 0},
    )

    xproto.ChangeWindowAttributes(X, wid, xproto.CwBackPixel|xproto.CwEventMask,
        []uint32{0xffffffff, xproto.EventMaskExposure | xproto.EventMaskStructureNotify | xproto.EventMaskKeyPress | xproto.EventMaskKeyRelease},
    )

    err = xproto.MapWindowChecked(X, wid).Check()
    if err != nil {
        fmt.Printf("Checked Error for mapping window %d: %s\n", wid, err)
    } else {
        fmt.Printf("Map window %d successful!\n", wid)
    }
    //last_time := time.Unix(0, 0)

    for {
        var ev interface{}
        ev, xerr := X.WaitForEvent()
        if ev == nil && xerr == nil {
            fmt.Println("Both event and error are nil. Exiting...")
            return
        }
        if ev != nil {
            switch ev := ev.(type) {
                case xproto.ExposeEvent:
                    /*if time.Now().Before(last_time.Add( 5 * time.Second)) {
                        fmt.Println("Skip fast exposure event", time.Now(), last_time)
                        break
                    }
                    last_time = time.Now()*/

                    length := int32(ev.Width) * int32(ev.Height)
                    buf_size := 4096
                    fmt.Println("Event:", ev)
                    // Use PolyPoint to draw buffer of pixels
                    points := make([]xproto.Point, buf_size, buf_size)

                    total_buf := 0
                    buf_pos := 0
                    for pos := int32(0); pos < length; pos ++ {
                        x := uint16(pos) % ev.Width
                        y := uint16(pos) / ev.Width

                        // inline mandelbrot compute
                        c := complex(
                            float64(x) / (float64(ev.Width) / float64(4)) - 2.5,
                            (float64(ev.Height) - float64(y)) / (float64(ev.Height) / float64(4)) - 2.,
                        )
                        max_iter := 30
                        u := complex(0, 0)
                        iter := 0
                        for ; iter < max_iter; iter++ {
                            u = u * u + c
                            if math.Abs(real(u)) > 1e6 || math.Abs(imag(u)) > 1e6 {
                                break
                            }
                            iter ++
                        }
                        // Only draw pixel when serie is stable
                        if iter == max_iter {
                            if buf_pos == buf_size {
                                xproto.PolyPointChecked(X, xproto.CoordModeOrigin, drawable, foreground, points)
                                total_buf ++
                                buf_pos = 0
                            }
                            points[buf_pos] = xproto.Point{int16(x), int16(y)}
                            buf_pos ++
                        }
                    }
                    xproto.PolyPointChecked(X, xproto.CoordModeOrigin, drawable, foreground, points[:buf_pos])
                    fmt.Println("Drawn", total_buf + 1, "poly points")
                case xproto.KeyPressEvent:
                    return
            }

        }
        if xerr != nil {
            fmt.Printf("Error: %s\n", xerr)
        }
    }
}
