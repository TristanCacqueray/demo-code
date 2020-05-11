#!/bin/env hy
; Licensed under the Apache License, Version 2.0 (the "License"); you may
; not use this file except in compliance with the License. You may obtain
; a copy of the License at
;
;      http://www.apache.org/licenses/LICENSE-2.0
;
; Unless required by applicable law or agreed to in writing, software
; distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
; WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
; License for the specific language governing permissions and limitations
; under the License.

;; This fixes https://github.com/hylang/hy/issues/1753
(import glumpy hy sys os io json time numpy subprocess)
(setv sys.executable hy.sys_executable)

(import [hy2glsl [hy2glsl library]]
        [utils.gamegl [usage FragmentShader]]
        [utils.audio [Audio SpectroGram]]
        [utils.midi [Midi]]
        [utils.modulations [combine PitchModulator AudioModulator]])

(defn r [color] (get color 0))
(defn g [color] (get color 1))
(defn b [color] (get color 2))

(defn shader [&optional map-mode super-sampling]
  (setv max-iter 12.0
        color-ratio 50.2
        escape (** 10.0 2)
        col [0 0.4 0.7]
        color
        `(shader
           (uniform float color_power)
           (uniform float max_iter)
           ~(when (not map-mode) '(uniform vec2 seed))
           (defn color [coord]
             (setv idx 0.0)
             (setv z ~(if-not map-mode 'coord '(vec2 0.0)))
             (setv c ~(if-not map-mode 'seed 'coord))
             (setv ci 0.0)
             ;; Orbit trap based on https://www.shadertoy.com/view/4lGXDK
             ;; Created by Piotr Borys - utak3r/2017
             (setv trap (vec4 1e20))
             (while (< idx max_iter)
               (if (> (dot z z) ~escape)
                   (break))
               (setv z (+ (cSquare z) c))
               (setv idx (+ idx 1.0)))
             (setv ci (- (+ idx 1.0) (log2 (* 0.5 (log2 (dot z z))))))
             (setv ci (sqrt (/ ci color_power)))
       (return (vec3
                 (+ 0.5 (* 0.5 (cos (+ (* 6.2831 ci) ~(r col)))))
                 (+ 0.5 (* 0.5 (cos (+ (* 6.2831 ci) ~(g col)))))
                 (+ 0.5 (* 0.5 (cos (+ (* 6.2831 ci) ~(b col))))))))))
  (hy2glsl
    (library.fragment-plane color
                            :invert-xy (not map-mode)
                            :super-sampling super-sampling
                            :center-name (if map-mode 'map_center 'center)
                            :range-name (if map-mode 'map_range 'range))))

;; TODO: move those common procedures to a module
(defn linspace [start end length]
  (numpy.linspace start end length))
(defn logspace [start end length]
  (numpy.logspace (numpy.log10 start) (numpy.log10 end) length))

(defmacro scene [name next &rest body]
  `(do
     (setv scene-idx (inc scene-idx))
     (when (and (>= frame begin) (< frame (get scenes ~name)))
       (setv scene-name ~name)
       (print scene-name :end ": ")
       (setv scene-length (- (get scenes ~name) begin))
       (setv scene-pos (- frame begin))
       (setv scene-ratio (/ scene-pos scene-length))
       (setv next ~next)
       (when (= scene-pos 0)
         (assoc params "base-seed" [(get (get params "seed") 0)
                                    (get (get params "seed") 1)]))
       ~@body)
     (when (= frame (get scenes ~name))
       (setv (get prev-seed 0) (get (get params "seed") 0)
             (get prev-seed 1) (get (get params "seed") 1)))
     (setv begin (get scenes ~name))))
(defmacro pan [proc start stop]
  `(get (~proc ~start ~stop scene-length) scene-pos))
(defmacro move [object mod ratio]
  `(do
     (setv ~object (+ ~object (* ~mod ~ratio)))))
(defmacro move-seed [axis mod &optional offset]
  `(do
     (when ~mod
     (move (get (get params ~(if offset "base-seed" "seed")) ~axis) ~mod
           (get prev-seed ~axis) (get next ~axis))
     ~(when offset
        `(setv (get (get params "seed") ~axis)
               (+ (get (get params "base-seed") ~axis)
                  ~offset))))))

;; The main animation code
(defn anim [params audio midi]
  (defn set-param [name value]
    (assoc params name value))
  (defn update [name change]
    (set-param name (+ (get params name) change)))
  (defn update-list [name index change]
    (assoc (get params name)
           index
           (+ (get (get params name) index) change)))

  (setv scene-mod
        {
         "bass" (PitchModulator "livet bass" :decay 20)
         "bass-comp" (PitchModulator "livet LCH")
         "scream" (PitchModulator "livet HCH")
         "rhode" (PitchModulator "livet FX")
         "snare" (PitchModulator "psy snare" :decay 30)
         "perc" (combine (PitchModulator "Big kit kick")
                         (PitchModulator "Teckno KICK"))
         "low" (AudioModulator [575 1000])
         "mid" (AudioModulator [100 200])
         })
  (setv scenes {
                "intro" 3500
               })

  ;; Pre-compute scene modulation content to be used by the move macro
  (setv pre-compute {})
  (setv audio.play False idx 0)

  ;; Starting parameters
  (setv prev-seed [-0.09542549812975187, -1.130157373495923])
  (setv prev-seed [-1.2396664226493714, -0.376572715308])
  (setv start-color 32.0)
  (assoc params
         "map_center" [-0.5 0.0]
         "map_range" 2.4
         "center" [0. 0.]
         "range" 3.10
         "seed" [(get prev-seed 0) (get prev-seed 1)]
         "color_power" start-color
         "max_iter" 12.0
         )
  (fn [frame]
    (spectre.transform (.get audio frame))
    (setv begin 0 scene-idx 0 midi-events (.get midi (+ 124 frame))
          ;; TODO: figure out a way to generate those variable
          bass-comp ((get scene-mod "bass-comp") midi-events)
          scream ((get scene-mod "scream") midi-events)
          rhode ((get scene-mod "rhode") midi-events)
          perc ((get scene-mod "perc") midi-events)
          snare ((get scene-mod "snare") midi-events)
          bass ((get scene-mod "bass") midi-events)
          low ((get scene-mod "low") spectre)
          mid ((get scene-mod "mid") spectre))

    (when midi-events
      (print midi-events))

    (scene "intro" [-0.7466245477796871, -1.929687395146181]
           (move (get (get params "seed") 0) low 1e-2)
           ;; This moves the some
           (set-param "range" (pan logspace 2.4 1.2)))))


(setv args (usage))
(.update args.params
         {"mods" {"color_power" {"type" "ratio"
                                 "sliders" True
                                 "min" 0
                                 "max" 150
                                 "resolution" 0.1}
                  "max_iter" {"type" "ratio"
                                 "sliders" True
                                 "min" 1
                                 "max" 200
                                 "resolution" 1}

                  }})

(setv
  audio (Audio args.wav args.fps)
  midi (Midi args.midi args.fps)
  spectre (SpectroGram audio.blocksize)
  mod (anim args.params audio midi)
  scene (FragmentShader args (shader :super-sampling args.super-sampling)
                        :title "Fractal")
  mapscene (if (not args.record)
               (FragmentShader args (shader :map-mode True :super-sampling 1)
                               :winsize (list (numpy.divide args.winsize 4))
                               :title "Map"))
  backend glumpy.app.__backend__
  clock (glumpy.app.__init__ :backend backend :framerate args.fps)
  scene.alive True
  scene.paused args.paused
  frame args.skip)

(setv audio.play False)
(for [skip (range args.skip)]
  (mod skip))
(setv audio.play (not args.record))

(while (and scene.alive (< frame 3700))
  (setv start-time (time.monotonic)
        updated False)
  (when (not scene.paused)
      (mod frame))
  (when (scene.update frame)
    (scene.render frame)
    (scene.controller.update_sliders)
    (setv scene.draw False updated True)
    (if args.record
        (scene.capture (os.path.join args.record
                                     (.format "{:04d}.png" frame)))))
  (when (and (not args.record) scene.alive (mapscene.update frame))
    (mapscene.render frame)
    (setv mapscene.draw False))
  (when updated
    (print (.format "{:04}: {:.2f} sec '{}'"
                    frame
                    (- (time.monotonic) start-time)
                    (json.dumps (scene.controller.get) :sort_keys True))))

  (when (not scene.paused)
    (setv frame (inc frame)))
  (backend.process (clock.tick)))

(when args.record
    (setv ffmpeg-command [
                "ffmpeg"
                "-y"
                "-framerate" (str args.fps)
                "-i" (.format "{}/%04d.png" args.record)
                "-i" args.wav
                "-c:a" "libvorbis" "-c:v" "copy"
                (.format "{}/render.mp4" args.record)
                ])
    (print "Running" (.join " " ffmpeg-command))
    (.wait (subprocess.Popen ffmpeg-command)))
