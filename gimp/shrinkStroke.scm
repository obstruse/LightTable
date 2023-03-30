(define (script-fu-shrink-stroke inImage inDrawable inShrinkth inColor inLoop inWidth ) 
    (let* (
           (theImage inImage)
           (theDrawable inDrawable)
           (theShrinkth inShrinkth)
           (theColor inColor)
           (theLoop inLoop)
           (theWidth inWidth)
           ;(theDirname inDirname)
           ;(fileName "")
           )
      (gimp-image-undo-group-start theImage)

      (gimp-context-set-foreground theColor)
      (gimp-context-set-line-width theWidth)
      (gimp-context-set-stroke-method 0)
      (gimp-context-set-antialias FALSE)

      (while (> theLoop 0)
          ;(gimp-message (number->string theLoop))
          ;(gimp-message (number->string(car (gimp-context-get-line-width))))
          (gimp-selection-shrink theImage theShrinkth)
          (gimp-drawable-edit-stroke-selection theDrawable)
          ;(set! fileName (string-append theDirname "/shrinkth-" (number->string ( + 100 theLoop)) ".png" ))
          ;(file-png-save 1 theImage theDrawable fileName fileName 0 9 0 0 0 0 0)
          (set! theLoop (- theLoop 1))
      )

      (gimp-displays-flush)
      (gimp-image-undo-group-end theImage)

  )
)

; Register the function with GIMP:

(script-fu-register "script-fu-shrink-stroke"
  "Shrink Stroke..."
  "Shrink the selection and stroke it"
  "Bill Neisius"
  ""
  "24 Jan 2023"
  ""
  SF-IMAGE       "The image"   0
  SF-DRAWABLE    "The layer"   0
  SF-ADJUSTMENT  "Shrinkth"      '(20 1 100 1 1 0 0)
  SF-COLOR       "Color"       '(255 255 255)
  SF-ADJUSTMENT  "Loop"        '(1 1 100 1 1 0 0)
  SF-ADJUSTMENT  "Width"       '(1 1 100 1 1 0 0)
  ;SF-DIRNAME     "Directory for save" "./"
)

(script-fu-menu-register "script-fu-shrink-stroke" "<Image>/Filters")

