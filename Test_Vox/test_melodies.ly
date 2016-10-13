\version "2.18.2"

global = {
  \key c \major
  \time 4/4
}

bassVoice = \relative c {
  \global
  \dynamicUp
  c'4. g8 a4 e4 | d4 e4 f2 | c'4. g8 a4 e4 | b4 d4 c2
  
}

verse = \lyricmode {
  % Lyrics follow here.
  
}

\score {
  \new Staff \with {
    instrumentName = "Bass"
    midiInstrument = "choir aahs"
  } { \clef bass \bassVoice }
  \addlyrics { \verse }
  \layout { }
  \midi {
    \tempo 4=100
  }
}
