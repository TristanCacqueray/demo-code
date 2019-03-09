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

;; Primitive procedures
(defn compose [f g]
  (fn [x] (f (g x))))

(defn repeat [f n]
  (if (= n 1)
      f
      (compose f (repeat f (dec n)))))

(defn decay-damp [prev new damp]
  (if (> new prev)
      new
      (damp prev new)))

(defn average [x y]
  (/ (+ x y) 2))

(defn average-decay [prev new]
  (decay-damp prev new average))

(defn ratio-decay [ratio]
  (fn [prev new]
    (decay-damp
      prev
      new
      (fn [prev new] (- prev (/ (- prev new) ratio))))))

; Input selector
(defn midi-track-selector [track-name]
  (fn [input]
    (for [event input]
      (if (= (.get event "track") track-name)
          (return (.get event "ev"))))
    []))

(defn midi-pitch-selector [selector]
  (fn [input]
    (for [event (selector input)]
      (if (= (.get event "type") "chords")
          (return (.get event "pitch"))))))

; Higher level procedures
(defn band-selector [lower-freq upper-freq]
  (import [numpy :as np])
  (fn [input]
    (setv band (cut input.band lower-freq upper-freq))
    (cond [(.all (= band 0)) 0]
          [True (np.mean band)])))

(defn midi-pitch-max [selector]
  (fn [input]
    (setv pitch (selector input))
    (if pitch
        (/ (max (.values pitch)) 127)
        0)))

(defn midi-note [selector note]
  (fn [input]
    (setv pitch (selector input))
    (if (and pitch (in note pitch))
        (get pitch note)
        0)))

(defn Modulator [selector modulator &optional [init 0.0]]
  (setv prev init)
  (fn [input]
    ;; A bit of impurity to keep the previous value
    (nonlocal prev)
    (setv val (modulator prev (selector input)))
    (setv prev val)
    val))

; Public procedures
(defn PitchModulator [track-name &optional [decay 10]]
  (Modulator
    (midi-pitch-max (midi-pitch-selector (midi-track-selector track-name)))
    (ratio-decay decay)))

(defn AudioModulator [band &optional [decay 10]]
  (Modulator
    (band-selector (first band) (last band))
    (ratio-decay decay)))

(defn NoteModulator [track-name note &optional [decay 10]]
  (Modulator
    (midi-note (midi-pitch-selector (midi-track-selector track-name)) note)
    (ratio-decay decay)))
