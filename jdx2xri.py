#!/usr/bin/python
import sys
if len(sys.argv) < 2:
    print 'Error: Need a filename of JCAMP-DX (.dx/.jdx)'
    print 'Usage:'
    print 'python', sys.argv[0], 'filename.dx'
    sys.exit(1)
with open(sys.argv[1], 'r') as jdx:
    factors = [1.0, 1.0, 1.0]
    realOn = False
    imagOn = False
    yspercol = None
    x0 = None
    xN = None
    dT = None
    reals = []
    imags = []
    for line in jdx.readlines():
        if line.startswith('##'):
            ldr = line.split('=')[0].upper().translate(None, ' \n\t\r')
            val = line.split('=')[1].translate(None, '\n\t\r').strip(' ')
            if ldr == '##FACTOR':
                factors = map(float, val.split(',')[0:3])
            elif ldr == '##DATATABLE' and val.split(',')[0] == '(X++(R..R))':
                realOn = True
                imagOn = False
            elif ldr == '##DATATABLE' and val.split(',')[0] == '(X++(I..I))':
                imagOn = True
                realOn = False
            elif ldr == '##END' or ldr == '##ENDTUPLES':
                realOn = False
                imagOn = False
                break
        elif line.startswith('$$'):
            pass
        else:
            if realOn:
                vals = map(float, line.split())
                if xN == None and x0 != None:
                    xN = vals[0]
                    dT = (xN - x0) / yspercol
                if x0 == None:
                    x0 = vals[0]
                if yspercol == None:
                    yspercol = len(vals[1:])
                reals = reals + vals[1:]
            if imagOn:
                imags = imags + vals[1:]
    jdx.close()
    if len(reals) != len(imags) or dT == None or x0 == None:
        print 'Could not read .dx properly'
        sys.exit(1)
    outname = sys.argv[1].strip(' ') + '.dat'
    output = open(outname, 'w')
    x = [(x0 + i * dT) * factors[0] for i in range(len(reals))]
    reals[:] = [y * factors[1] for y in reals]
    imags[:] = [y * factors[2] for y in imags]
    for i in range(len(x)):
        output.write('%f %f %f\r\n' % (x[i], reals[i], imags[i]))
    output.close()
    print 'File ' + outname + ' saved.'
sys.exit(0)

##FACTOR=0.00115999997069593519,0.00000170124001683638,0.00000170124001683638,1
##PAGE=N=1
##DATA TABLE= (X++(R..R)), XYDATA
#      0.00000000     2147483000      648685570     -228998040      344999634
##PAGE=N=2
##DATA TABLE= (X++(I..I)), XYDATA
#      0.00000000        -442162     -372730333     1290294097     1331355703
##END NTUPLES=NMR FID
##END=
