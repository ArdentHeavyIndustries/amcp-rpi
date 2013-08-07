#!/usr/bin/env python

import effects, struct, time

model = struct.pack("fff", 1,2,3) * (40*64)

matrix = (1,0,0,0,
		  0,1,0,0,
		  0,0,1,0,
		  0,0,0,1)

baseColor = (0.5, 0.5, 0.5)
noiseColor = (0.2, 0.2, 0.2)
lightning = [(1,2,3,4,5,6,7)]

n = frames = 100
t1 = time.time()
while n:
	n -= 1
	str(effects.cloud.render(model, matrix, baseColor, noiseColor, lightning))
t2 = time.time()
print "%f fps" % (frames / (t2-t1))

