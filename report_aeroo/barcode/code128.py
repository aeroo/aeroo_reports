# Copyright (c) 2009-2011 Alistek Ltd (http://www.alistek.com) All Rights Reserved.
#                    General contacts <info@alistek.com>
# This list was cut'n'pasted verbatim from the "Code 128 Specification Page"
# at http://www.adams1.com/pub/russadam/128code.html

codelist="""0 	SP 	SP 	00 	2 1 2 2 2 2
1 	! 	! 	01 	2 2 2 1 2 2
2 	" 	" 	02 	2 2 2 2 2 1
3 	# 	# 	03 	1 2 1 2 2 3
4 	$ 	$ 	04 	1 2 1 3 2 2
5 	% 	% 	05 	1 3 1 2 2 2
6 	& 	& 	06 	1 2 2 2 1 3
7 	' 	' 	07 	1 2 2 3 1 2
8 	( 	( 	08 	1 3 2 2 1 2
9 	) 	) 	09 	2 2 1 2 1 3
10 	* 	* 	10 	2 2 1 3 1 2
11 	+ 	+ 	11 	2 3 1 2 1 2
12 	, 	, 	12 	1 1 2 2 3 2
13 	- 	- 	13 	1 2 2 1 3 2
14 	. 	. 	14 	1 2 2 2 3 1
15 	/ 	/ 	15 	1 1 3 2 2 2
16 	0 	0 	16 	1 2 3 1 2 2
17 	1 	1 	17 	1 2 3 2 2 1
18 	2 	2 	18 	2 2 3 2 1 1
19 	3 	3 	19 	2 2 1 1 3 2
20 	4 	4 	20 	2 2 1 2 3 1
21 	5 	5 	21 	2 1 3 2 1 2
22 	6 	6 	22 	2 2 3 1 1 2
23 	7 	7 	23 	3 1 2 1 3 1
24 	8 	8 	24 	3 1 1 2 2 2
25 	9 	9 	25 	3 2 1 1 2 2
26 	: 	: 	26 	3 2 1 2 2 1
27 	; 	; 	27 	3 1 2 2 1 2
28 	< 	< 	28 	3 2 2 1 1 2
29 	= 	= 	29 	3 2 2 2 1 1
30 	> 	> 	30 	2 1 2 1 2 3
31 	? 	? 	31 	2 1 2 3 2 1
32 	@ 	@ 	32 	2 3 2 1 2 1
33 	A 	A 	33 	1 1 1 3 2 3
34 	B 	B 	34 	1 3 1 1 2 3
35 	C 	C 	35 	1 3 1 3 2 1
36 	D 	D 	36 	1 1 2 3 1 3
37 	E 	E 	37 	1 3 2 1 1 3
38 	F 	F 	38 	1 3 2 3 1 1
39 	G 	G 	39 	2 1 1 3 1 3
40 	H 	H 	40 	2 3 1 1 1 3
41 	I 	I 	41 	2 3 1 3 1 1
42 	J 	J 	42 	1 1 2 1 3 3
43 	K 	K 	43 	1 1 2 3 3 1
44 	L 	L 	44 	1 3 2 1 3 1
45 	M 	M 	45 	1 1 3 1 2 3
46 	N 	N 	46 	1 1 3 3 2 1
47 	O 	O 	47 	1 3 3 1 2 1
48 	P 	P 	48 	3 1 3 1 2 1
49 	Q 	Q 	49 	2 1 1 3 3 1
50 	R 	R 	50 	2 3 1 1 3 1
51 	S 	S 	51 	2 1 3 1 1 3
52 	T 	T 	52 	2 1 3 3 1 1
53 	U 	U 	53 	2 1 3 1 3 1
54 	V 	V 	54 	3 1 1 1 2 3
55 	W 	W 	55 	3 1 1 3 2 1
56 	X 	X 	56 	3 3 1 1 2 1
57 	Y 	Y 	57 	3 1 2 1 1 3
58 	Z 	Z 	58 	3 1 2 3 1 1
59 	[ 	[ 	59 	3 3 2 1 1 1
60 	\\ 	\\ 	60 	3 1 4 1 1 1
61 	] 	] 	61 	2 2 1 4 1 1
62 	^ 	^ 	62 	4 3 1 1 1 1
63 	_ 	_ 	63 	1 1 1 2 2 4
64 	NUL 	' 	64 	1 1 1 4 2 2
65 	SOH 	a 	65 	1 2 1 1 2 4
66 	STX 	b 	66 	1 2 1 4 2 1
67 	ETX 	c 	67 	1 4 1 1 2 2
68 	EOT 	d 	68 	1 4 1 2 2 1
69 	ENQ 	e 	69 	1 1 2 2 1 4
70 	ACK 	f 	70 	1 1 2 4 1 2
71 	BEL 	g 	61 	1 2 2 1 1 4
72 	BS 	h 	72 	1 2 2 4 1 1
73 	HT 	i 	73 	1 4 2 1 1 2
74 	LF 	j 	74 	1 4 2 2 1 1
75 	VT 	k 	75 	2 4 1 2 1 1
76 	FF 	l 	76 	2 2 1 1 1 4
77 	CR 	m 	77 	4 1 3 1 1 1
78 	SO 	n 	78 	2 4 1 1 1 2
79 	SI 	o 	79 	1 3 4 1 1 1
80 	DLE 	p 	80 	1 1 1 2 4 2
81 	DC1 	q 	81 	1 2 1 1 4 2
82 	DC2 	r 	82 	1 2 1 2 4 1
83 	DC3 	s 	83 	1 1 4 2 1 2
84 	DC4 	t 	84 	1 2 4 1 1 2
85 	NAK 	u 	85 	1 2 4 2 1 1
86 	SYN 	v 	86 	4 1 1 2 1 2
87 	ETB 	w 	87 	4 2 1 1 1 2
88 	CAN 	x 	88 	4 2 1 2 1 1
89 	EM 	y 	89 	2 1 2 1 4 1
90 	SUB 	z 	90 	2 1 4 1 2 1
91 	ESC 	{ 	91 	4 1 2 1 2 1
92 	FS 	| 	92 	1 1 1 1 4 3
93 	GS 	} 	93 	1 1 1 3 4 1
94 	RS 	~ 	94 	1 3 1 1 4 1
95 (Hex 7F) 	US 	DEL 	95 	1 1 4 1 1 3
96 (Hex 80) 	FNC 3 	FNC 3 	96 	1 1 4 3 1 1
97 (Hex 81) 	FNC 2 	FNC 2 	97 	4 1 1 1 1 3
98 (Hex 82) 	SHIFT 	SHIFT 	98 	4 1 1 3 1 1
99 (Hex 83) 	CODE C 	CODE C 	99 	1 1 3 1 4 1
100 (Hex 84) 	CODE B 	FNC 4 	CODE B 	1 1 4 1 3 1
101 (Hex 85) 	FNC 4 	CODE A 	CODE A 	3 1 1 1 4 1
102 (Hex 86) 	FNC 1 	FNC 1 	FNC 1 	4 1 1 1 3 1"""




other="""103 (Hex 87) 	START (Code A) 	2 1 1 4 1 2
104 (Hex 88) 	START (Code B) 	2 1 1 2 1 4
105 (Hex 89) 	START (Code C) 	2 1 1 2 3 2
106 	STOP 	2 3 3 1 1 1 2"""


codes={}
values={}
for l in codelist.split('\n'):
    l.strip()    
    num,a1,b1,c1,code=l.split('\t')
    num=int(num.split(' ')[0])
    values[num]=[int(x) for x in code.split()]
    codes[b1.strip()]=num

codes[' ']=codes['SP']

for l in other.split('\n'):
    l.strip()
    num,name,code=l.split('\t')
    num=int(num.split(' ')[0])
    values[num]=[int(x) for x in code.split()]
    codes[name.strip()]=num

def encode_message(msg):
    startnum=codes['START (Code B)']
    message=values[startnum][:]
    chksum=startnum
    mult=1
    for c in msg:
        if not codes.has_key(c):
            raise "No code for "+c
        chksum=chksum+mult*codes[c]
        mult=mult+1
        message=message+values[codes[c]]

    chksum=chksum%103
    
    message=message+values[chksum]
    message=message+values[codes['STOP']]

    return message


import os
from PIL import Image
def get_code(message,xw=1,h=100,rotate=None):
    """ message is message to code.
        xw is horizontal multiplier (in pixels width of narrowest bar)
        h is height in pixels.

        Returns a Python Imaging Library object."""

    widths=[xw*20]+encode_message(message)+[xw*20]
    
    bits=[]
    i=1
    for w in widths:
        bits=bits+[i]*w*xw
        i=1-i

    #print len(bits)
    #print bits
    
    i=Image.new('1',(len(bits),h),1)

    for b in range(len(bits)):
        for y in range(h):
            i.putpixel((b,y),255*bits[b])

    return i


