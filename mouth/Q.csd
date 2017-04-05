; Q: Vox Output
;
; The bedrock of this file comes from the fof example in the Csound Opcode Help

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

alwayson "Note_Receiver"
giOSC OSCinit 6006
giSine    ftgen 1, 0, 16384, 10, 1
giSigmoid ftgen 2, 0, 1024,  19, 0.5, 0.5, 270, 0.5

instr Note_Receiver
	kfund init 0
	kmidipitch init 0
	knotedur init 0
	kampmain init 0
	kf1 init 0
	kf2 init 0
	kf3 init 0
	kf4 init 0
	kf5 init 0
	
	; Listen for OSC messages
	ktrig OSClisten giOSC, "/note", "fffiiiii", kmidipitch, knotedur, kampmain, kf1, kf2, kf3, kf4, kf5
	if (ktrig == 1) then
		kfund = cpsmidinn(kmidipitch)
		kres rand 10
		kfund = kfund + kres
		event "i", "Vox", 0, (knotedur / 1000.0), kfund, kampmain, kf1, kf2, kf3, kf4, kf5
	endif
endin

instr Vox
	; Values common to all of the formants.
	;koct init 0
	koctnum rand 5, 0.5, 0, 1      ; Randomly pick octave range to drop
						   ; Will determine amount of vocal fry
	koct   linseg   0,  p3*.1,  0,  p3*.8, i(koctnum),  p3*.1,  i(koctnum)
	print i(koctnum)
	kris init 0.003
	kdur init 0.02
	kdec init 0.007
	iolaps = 100
	itotdur = p3
	;kmidipitch = p4
	kfund = p4
	kampmain = p5
	
	kf1 = p6
	kf2 = p7
	kf3 = p8
	kf4 = p9
	kf5 = p10
		
	;kfund = cpsmidinn(kmidipitch)
	
	; First formant.
	k1amp = ampdb(0)
	;k1form line 800, p3, 350
	k1form init 800
	k1band line 80, itotdur, 50
	
	; Second formant.
	k2amp line ampdb(-4), itotdur, ampdb(-20)
	;k2form line 1150, p3, 1700
	k2form init 1150
	k2band line 90, itotdur, 100
	
	; Third formant.
	k3amp line ampdb(-20), itotdur, ampdb(-30)
	;k3form line 2800, p3, 2700
	k3form init 2800
	k3band init 120
	
	; Fourth formant.
	k4amp init ampdb(-36)
	;k4form line 3500, p3, 3700
	k4form init 3500
	k4band line 130, itotdur, 150
	
	; Fifth formant.
	k5amp init ampdb(-60)
	k5form init 4950
	k5band line 140, itotdur, 200
	
	k1newamp = k1amp * kampmain
	k2newamp = k2amp * kampmain
	k3newamp = k3amp * kampmain
	k4newamp = k4amp * kampmain
	k5newamp = k5amp * kampmain
	
	avibrato   oscil  0.5,  5,  1     ; Adds vibrato

	a1 fof k1newamp, kfund, kf1, koct, k1band, kris, kdur, kdec, iolaps, giSine, giSigmoid, itotdur, 0, 1
	a2 fof k2newamp, kfund+avibrato, kf2, koct, k2band, kris, kdur, kdec, iolaps, giSine, giSigmoid, itotdur
	a3 fof k3newamp, kfund, kf3, koct, k3band, kris, kdur, kdec, iolaps, giSine, giSigmoid, itotdur
	a4 fof k4newamp, kfund, kf4, koct, k4band, kris, kdur, kdec, iolaps, giSine, giSigmoid, itotdur
	a5 fof k5newamp, kfund, kf5, koct, k5band, kris, kdur, kdec, iolaps, giSine, giSigmoid, itotdur
	
	; Combine all of the formants together
	asig sum (a1+a2+a3+a4+a5)
	outs asig, asig
endin

</CsInstruments>
<CsScore>
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
