for f in *.wav; do sox $f -n stat |& grep '^Rough' | echo $(awk '{print $3}')","$f >> rfreq.csv
done


