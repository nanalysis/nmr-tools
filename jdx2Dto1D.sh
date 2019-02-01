#!/bin/bash
zero ()
{
k=${1:?"Number to print missing"}
j=${2:?"Number of digits missing"}
fin=1
h=1
dig=0
while [ $fin -eq 1 ]; do
  if [ $k -lt $((10**$h)) ]; then
    fin=2
    dig=$h
  else
    h=$(($h+1))
  fi
done
zero=$(($j-$dig))
zeros=''
for (( i=1 ; i<=$zero ; i++ )); do
  zeros=$zeros'0'
done
num=$zeros$k
echo $num
}

int () {
    printf "%.0f\n" "$@"
}

findline () 
{ 
  grep -n "$2" $1 | head -1 | sed 's/:/ /g' | awk '{print $1}' 
}

replaceline ()
{
  infile=$1
  outfile=$2
  pattern=$3
  newline=$4
  lnum=$(findline $infile "$pattern")
  if [ -n "$lnum" ]; then
    sed -n '1,'$(($lnum-1))'p' $infile > $outfile
    if [ -n "$newline" ]; then
      echo -e "$newline" >> $outfile
    fi
    sed -n $(($lnum+1))',$p' $infile >> $outfile
  fi
}

file=$1
name=$(echo $file | sed 's/\(.*\)\..*/\1/')
headend=$(findline $file "##DATATABLE=") 
tmp1=$(tempfile)
tmp2=$(tempfile)
#copy head to tmp1
sed -n '1,'$headend'p' $file > $tmp1
#replace 
replaceline $tmp1 $tmp2 "##JCAMP" "##JCAMP-DX=5.01 \$\$ Nanalysis NMReady v2.0.4\r"
replaceline $tmp2 $tmp1 "##NUMDIM" ""
replaceline $tmp1 $tmp2 "##DATA TYPE=" "##DATA TYPE=NMR FID\r"
replaceline $tmp2 $tmp1 "##\$EXPERIMENT" ""
replaceline $tmp1 $tmp2 "##\.NUCLEUS" ""
replaceline $tmp2 $tmp1 "##\$T..POINTS=" ""
replaceline $tmp1 $tmp2 "##\.PULSE SEQUENCE" ""
replaceline $tmp2 $tmp1 "##NTUPLES" "##NTUPLES=NMR FID\r"
#remove bruker F1
bruf1=$(findline $tmp1 "Bruker specific parameters for F1")
bruend=$(findline $tmp1 "End of Bruker specific parameters")
sed -n '1,'$(($bruf1-1))'p' $tmp1 > $tmp2
sed -n $(($bruend))',$p' $tmp1 >> $tmp2
#replace npoints
npoints=$(grep '##VAR_DIM' $tmp2 | head -1 | sed 's/=/ /g' | sed 's/,/ /g' | awk '{print $3}')
replaceline $tmp2 $tmp1 "##NPOINTS" "##NPOINTS=$npoints\r"
#find ntuples line
lntup=$(findline $tmp1 "##NTUPLES=")
sed -n '1,'$lntup'p' $tmp1 > $tmp2 
#write new stuff
echo -e "##VAR_NAME=TIME,FID/REAL,FID/IMAG,PAGE NUMBER\r" >> $tmp2
echo -e "##SYMBOL=X,R,I,N\r" >> $tmp2
echo -e "##VAR_TYPE=INDEPENDENT,DEPENDENT,DEPENDENT,PAGE\r" >> $tmp2
echo -e "##VAR_FORM=AFFN,AFFN,AFFN,AFFN\r" >> $tmp2
echo -e "##VAR_DIM=$npoints,$npoints,$npoints,2\r" >> $tmp2
echo -e "##UNITS=SECONDS,ARBITRARY UNITS,ARBITRARY UNITS,\r" >> $tmp2
grep "##MIN=" $tmp1 | head -1 | sed 's/=/ /g' | sed 's/,/ /g' | sed 's/\r//g' | awk '{print "##MIN="$3","$4","$5",1\r"}' >> $tmp2
grep "##MAX=" $tmp1 | head -1 | sed 's/=/ /g' | sed 's/,/ /g' | sed 's/\r//g' | awk '{print "##MAX="$3","$4","$5",2\r"}' >> $tmp2
grep "##FACTOR=" $tmp1 | head -1 | sed 's/=/ /g' | sed 's/,/ /g' | sed 's/\r//g' | awk '{print "##FACTOR="$3","$4","$5",1\r"}' >> $tmp2
l1=( $(grep -n "##DATATABLE= (T2++(R..R)), PROFILE" $file | sed 's/:/ /g' | awk '{print $1}') )
l2=( $(grep -n "##DATATABLE= (T2++(I..I)), PROFILE" $file | sed 's/:/ /g' | awk '{print $1}') )
n=${#l1[@]}
len=${#n}
for (( k=0 ; k<$n; k++ )); do
  i=${l1[$k]}
  j=${l2[$k]}
  tau=$(sed -n $(($i-2))'p' $file | sed 's/\r//g' | sed 's/##PAGE= T1=//g')
  newname=${name}_$(zero $(($k+1)) $len)_${tau}ms
  outname=${newname}.dx
  echo $outname
  cat $tmp2 > $outname
  #touch ${newname}.jdx
#  ln -s $outname ${newname}.jdx
  #put first
  sed -n $(($i-1))'p' $file >> $outname
  echo -e "##PAGE=N=1\r" >> $outname
  echo -e "##DATA TABLE= (X++(R..R)), XYDATA\r" >> $outname
  #put real dat
  sed -n $(($i+1))','$(($j-3))'p' $file >> $outname
  echo -e "##PAGE=N=2\r" >> $outname
  echo -e "##DATA TABLE= (X++(I..I)), XYDATA\r" >> $outname
  #put imag data
  if [ $k -lt $(($n-1)) ]; then
    ni=${l1[$(($k+1))]}
    sed -n $(($j+1))','$(($ni-3))'p' $file >>  $outname
    echo -e "##END NTUPLES=NMR FID\r" >> $outname
    echo -e "##END=\r" >> $outname
  else
    sed -n $(($j+1))',$p' $file >> $outname
  fi
done
rm -f $tmp1 $tmp2
exit 0
