; Vox Output
;
; The bedrock of this file comes from the fof example in the Csound Opcode Help
;
; Tasks:
;   -Figure out how to end notes by changing kamp at end of notes
;   -Add more formants for richer sound

<CsoundSynthesizer>
<CsOptions>
;-odac ;;;realtime audio out
;-iadc ;;;realtime audio in
</CsOptions>
<CsInstruments>

sr = 44100
ksmps = 128
nchnls = 2
0dbfs = 1

alwayson "Vox"       ; Vox instrument only ends when score ends/program stops running
giOSC OSCinit 6007
giSine    ftgen 1, 0, 16384, 10, 1
giSigmoid ftgen 2, 0, 1024,  19, 0.5, 0.5, 270, 0.5

instr Vox
	; Combine five formants together to create 
	; a transformation from an alto-"a" sound
	; to an alto-"i" sound.
	; Values common to all of the formants.
	koct init 0
	kris init 0.003
	kdur init 0.02
	kdec init 0.007
	iolaps = 100
	itotdur = 3600
	
	;kamp init 1
	kfund init 300
	knotedur init 3600
	
	;Listen for OSC messages
	ktrig OSClisten giOSC, "/note", "ff", kfund, knotedur
	
	; First formant.
	k1amp = ampdb(0)
	;k1form line 800, p3, 350
	k1form init 800
	k1band line 80, i(knotedur), 50
	
	; Second formant.
	k2amp line ampdb(-4), i(knotedur), ampdb(-20)
	;k2form line 1150, p3, 1700
	k2form init 1150
	k2band line 90, i(knotedur), 100
	
	; Third formant.
	k3amp line ampdb(-20), i(knotedur), ampdb(-30)
	;k3form line 2800, p3, 2700
	k3form init 2800
	k3band init 120
	
	; Fourth formant.
	k4amp init ampdb(-36)
	;k4form line 3500, p3, 3700
	k4form init 3500
	k4band line 130, i(knotedur), 150
	
	; Fifth formant.
	k5amp init ampdb(-60)
	k5form init 4950
	k5band line 140, i(knotedur), 200
	
	a1 fof k1amp, kfund, k1form, koct, k1band, kris, kdur, kdec, iolaps, giSine, giSigmoid, itotdur
	a2 fof k2amp, kfund, k2form, koct, k2band, kris, kdur, kdec, iolaps, giSine, giSigmoid, itotdur
	a3 fof k3amp, kfund, k3form, koct, k3band, kris, kdur, kdec, iolaps, giSine, giSigmoid, itotdur
	a4 fof k4amp, kfund, k4form, koct, k4band, kris, kdur, kdec, iolaps, giSine, giSigmoid, itotdur
	a5 fof k5amp, kfund, k5form, koct, k5band, kris, kdur, kdec, iolaps, giSine, giSigmoid, itotdur
	
	; Combine all of the formants together
	asig sum (a1+a2+a3+a4+a5) ;* 13000
	outs asig, asig
endin

</CsInstruments>
<CsScore>
e 3600 ; Program runs for an hour
</CsScore>
</CsoundSynthesizer>
<bsbPanel>
 <label>Widgets</label>
 <objectName/>
 <x>100</x>
 <y>100</y>
 <width>320</width>
 <height>240</height>
 <visible>true</visible>
 <uuid/>
 <bgcolor mode="nobackground">
  <r>255</r>
  <g>255</g>
  <b>255</b>
 </bgcolor>
</bsbPanel>
<bsbPresets>
</bsbPresets>
